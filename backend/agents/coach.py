"""
Coach Agent — produces the final actionable coaching report.
Takes Critic-validated findings, enriches with historical context from the DB,
and shapes everything into the final structured output.
"""
import json
import logging
from backend.agents.tools import search_historical_rounds
from backend.utils.gemini_client import _extract_json

logger = logging.getLogger(__name__)


class CoachAgent:
    def __init__(self, client, model="gemini-2.5-flash"):
        self.client = client
        self.model = model

    def run(self, validated_findings: dict, context: dict, examples: list = None) -> dict:
        """
        Produce the final coaching report.
        Enriches mistake advice with historical examples from past rounds.
        """
        atk    = context.get("attacking_team", "Attackers")
        defn   = context.get("defending_team", "Defenders")
        winner = context.get("winner", "Unknown")
        game   = context.get("game", "r6siege")
        mistakes = validated_findings.get("mistakes", [])

        # Fetch historical context per mistake category
        historical_str = ""
        seen = set()
        for m in mistakes:
            cat = m.get("category", "")
            if cat and cat not in seen:
                similar = search_historical_rounds(game, cat, limit=2)
                if similar:
                    historical_str += f"\n{cat.title()} — similar past mistakes:\n"
                    for s in similar:
                        historical_str += f"  · {s.get('description', '')} → {s.get('better_alternative', '')}\n"
                seen.add(cat)

        few_shot = ""
        if examples:
            few_shot = "\nHIGH-QUALITY REFERENCE ANALYSES (match this level of specificity):\n"
            for ex in examples:
                few_shot += f"---\n{ex.get('full_result', '')}\n---\n"

        prompt = f"""You are the final coaching agent producing the definitive report.
{atk} attacking, {defn} defending. {winner} won.

VALIDATED FINDINGS FROM ANALYSIS PIPELINE:
{json.dumps(validated_findings, indent=2)}
{historical_str}
{few_shot}

Your task:
- Keep all validated mistakes exactly as they are (do not add or remove any)
- Strengthen the better_alternative for each mistake using the historical context where relevant
- Write a sharp, specific summary and key_takeaway grounded in what happened
- Do NOT invent new mistakes or change timestamps

Return ONLY valid JSON:
{{
  "summary": "...",
  "loss_reason": "...",
  "phase_breakdown": {{
    "setup": "...",
    "mid_round": "...",
    "endgame": "..."
  }},
  "mistakes": [
    {{
      "team": "...",
      "category": "...",
      "severity": "...",
      "description": "...",
      "timestamp": <int>,
      "confidence": <2 or 3>,
      "better_alternative": "..."
    }}
  ],
  "strengths": ["..."],
  "key_takeaway": "..."
}}"""

        logger.info("  [Coach] Producing final coaching report...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt]
        )

        result = _extract_json(response.text)
        if not result:
            logger.warning("  [Coach] Could not parse response — using validated findings as final")
            return validated_findings

        logger.info(f"  [Coach] Report complete: {len(result.get('mistakes', []))} mistakes, "
                    f"{len(result.get('strengths', []))} strengths")
        return result
