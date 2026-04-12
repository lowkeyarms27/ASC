"""
Debater Agent — challenges Tactician findings with adversarial reasoning.

For each finding, the Debater tries to poke holes in it using the Observer's
event log as evidence. It produces a challenge for each contested finding.
The Critic then receives both the findings AND the debate to make a final ruling.

This is more rigorous than a one-way review: findings must survive an active
challenge, not just pass a single validation pass.
"""
import json
import logging
from backend.utils.gemini_client import _extract_json

logger = logging.getLogger(__name__)


class DebaterAgent:
    def __init__(self, client, model="gemini-2.5-flash"):
        self.client = client
        self.model  = model

    def run(self, tactical_findings: dict, event_log: dict, context: dict) -> dict:
        """
        Challenge each Tactician finding.
        Returns tactical_findings with a 'debate' field added to each mistake:
          - verdict: "supported" | "contested" | "unsupported"
          - challenge: what the Debater argued against it
          - rebuttal: best counter-argument in the finding's favour
        """
        mistakes = tactical_findings.get("mistakes", [])
        if not mistakes:
            return tactical_findings

        gemini_log      = event_log.get("gemini_log", "")
        pegasus_summary = event_log.get("pegasus_summary", "")
        atk             = context.get("attacking_team", "Attackers")
        defn            = context.get("defending_team", "Defenders")

        prompt = f"""You are an adversarial debate judge reviewing AI-generated esports coaching findings.
{atk} are attacking, {defn} are defending.

FACTUAL EVENT LOG (ground truth):
{gemini_log}

PEGASUS REFERENCE:
{pegasus_summary}

TACTICIAN FINDINGS TO CHALLENGE:
{json.dumps(mistakes, indent=2)}

For each finding, actively try to argue AGAINST it using the event log.
Ask: Is there evidence at that timestamp? Could a different cause explain it?
Is the tactical interpretation the only reasonable one? Is the severity justified?

Then give the strongest counter-argument IN FAVOUR of the finding.

Return ONLY valid JSON — a list with one entry per finding in the same order:
[
  {{
    "finding_index": <int — 0-based index matching the input list>,
    "verdict": "supported | contested | unsupported",
    "challenge": "the strongest argument AGAINST this finding based on the event log",
    "rebuttal": "the strongest argument FOR this finding",
    "confidence_adjustment": <-1, 0, or +1 — whether debate weakens, maintains, or strengthens confidence>
  }}
]

Be genuinely adversarial. Findings with no event-log evidence should be "unsupported".
Well-grounded findings with clear timestamps should be "supported".
Ambiguous ones are "contested"."""

        logger.info(f"  [Debater] Challenging {len(mistakes)} finding(s)...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt]
        )

        debates = _extract_json(response.text)
        if not isinstance(debates, list):
            logger.warning("  [Debater] Could not parse debate — passing findings through unchanged")
            return tactical_findings

        # Attach debate results to each mistake
        debate_map = {d.get("finding_index"): d for d in debates if isinstance(d, dict)}
        enriched_mistakes = []
        dropped = 0

        for i, m in enumerate(mistakes):
            debate = debate_map.get(i, {})
            verdict = debate.get("verdict", "supported")

            if verdict == "unsupported":
                dropped += 1
                logger.info(f"  [Debater] Dropped finding {i} (unsupported): {m.get('description','')[:60]}")
                continue

            m["debate"] = {
                "verdict":              verdict,
                "challenge":            debate.get("challenge", ""),
                "rebuttal":             debate.get("rebuttal", ""),
                "confidence_adjustment": debate.get("confidence_adjustment", 0),
            }
            # Apply confidence adjustment
            adj = debate.get("confidence_adjustment", 0)
            m["confidence"] = max(2, min(3, m.get("confidence", 2) + adj))
            enriched_mistakes.append(m)

        logger.info(f"  [Debater] {len(enriched_mistakes)} survived debate, {dropped} dropped as unsupported")
        return {**tactical_findings, "mistakes": enriched_mistakes}
