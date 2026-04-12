"""
Critic Agent — validates Tactician findings against the Observer's event log.
Challenges unsupported claims, removes hallucinated findings, and scores confidence.
Accepts a configurable confidence_threshold so coaches can tune strictness.
"""
import json
import logging
from backend.utils.gemini_client import _extract_json
from backend.utils.nvidia_client import verify_frame
from backend.utils.video_processor import extract_frame_b64

logger = logging.getLogger(__name__)


class CriticAgent:
    def __init__(self, client, model="gemini-2.5-flash"):
        self.client = client
        self.model  = model

    def run(self, tactical_findings: dict, event_log: dict, context: dict,
            clip_path: str = None, confidence_threshold: float = 0.75) -> dict:
        """
        Review each Tactician finding against the Observer event log.
        Returns: {validated_mistakes, removed_count, confidence, flags, revised_findings}
        """
        atk      = context.get("attacking_team", "Attackers")
        defn     = context.get("defending_team", "Defenders")
        mistakes = tactical_findings.get("mistakes", [])

        if not mistakes:
            return {
                "validated_mistakes": [],
                "removed_count":      0,
                "confidence":         1.0,
                "flags":              [],
                "revised_findings":   tactical_findings,
            }

        gemini_log      = event_log.get("gemini_log", "")
        pegasus_summary = event_log.get("pegasus_summary", "")

        prompt = f"""You are a critical reviewer of AI-generated esports coaching analysis.
{atk} attacking, {defn} defending.

FACTUAL EVENT LOG (ground truth from Observer):
{gemini_log}

PEGASUS SUMMARY (secondary reference):
{pegasus_summary}

TACTICIAN FINDINGS TO REVIEW:
{json.dumps(mistakes, indent=2)}

For each mistake, determine:
1. Is it supported by the event log? Is there evidence at or near that timestamp?
2. Is the tactical interpretation reasonable given the facts?
3. Does the timestamp seem plausible for this type of event?

Be strict: remove findings not clearly grounded in the event log.
Retain findings that are well-supported even if you'd phrase them differently.
The current confidence threshold is {confidence_threshold:.0%} — flag any findings below this.

Return ONLY valid JSON:
{{
  "validated_mistakes": [<accepted mistake objects — include all original fields unchanged>],
  "removed_mistakes": [<brief description of each removed finding and why>],
  "confidence": <0.0 to 1.0 — how confident that validated findings are accurate>,
  "flags": [<int timestamps that need closer re-examination if confidence < {confidence_threshold:.2f}>]
}}"""

        logger.info(f"  [Critic] Reviewing {len(mistakes)} finding(s) (threshold={confidence_threshold:.0%})...")
        response = self.client.models.generate_content(
            model=self.model, contents=[prompt]
        )

        result = _extract_json(response.text)
        if not result:
            logger.warning("  [Critic] Could not parse response — trusting Tactician findings")
            return {
                "validated_mistakes": mistakes,
                "removed_count":      0,
                "confidence":         0.7,
                "flags":              [],
                "revised_findings":   tactical_findings,
            }

        if clip_path and result.get("flags"):
            result = self._visual_verify_flags(result, mistakes, clip_path)

        validated  = result.get("validated_mistakes", mistakes)
        removed    = len(mistakes) - len(validated)
        confidence = result.get("confidence", 0.7)
        flags      = result.get("flags", [])

        if removed:
            logger.info(f"  [Critic] Removed {removed} unsupported finding(s)")
        logger.info(f"  [Critic] Confidence: {confidence:.0%} | Flags: {flags}")

        revised = {**tactical_findings, "mistakes": validated}
        return {
            "validated_mistakes": validated,
            "removed_count":      removed,
            "confidence":         confidence,
            "flags":              flags,
            "revised_findings":   revised,
        }

    def _visual_verify_flags(self, critic_result: dict, all_mistakes: list, clip_path: str) -> dict:
        """Use nemotron-nano-12b-v2-vl to visually verify flagged timestamps."""
        flags     = critic_result.get("flags", [])
        validated = list(critic_result.get("validated_mistakes", []))
        valid_ts  = {m.get("timestamp", -1) for m in validated}

        for flag in flags[:3]:
            ts = int(flag) if isinstance(flag, (int, float)) else 0
            if ts <= 0:
                continue

            flagged = next(
                (m for m in all_mistakes if abs(m.get("timestamp", -999) - ts) <= 5), None
            )
            if not flagged or ts in valid_ts:
                continue

            frames = []
            for offset in [-2, 0, 2]:
                f = extract_frame_b64(clip_path, max(0, ts + offset))
                if f:
                    frames.append(f)
            if not frames:
                continue

            question = (
                f"At approximately {ts} seconds, did the following happen?\n"
                f"{flagged.get('description', '')}\n"
                f"Answer yes or no, then briefly explain what you see in these frames."
            )
            logger.info(f"  [Critic] nemotron-nano visual check at {ts}s...")
            answer = verify_frame(frames, question)

            if answer and answer.lower().startswith("yes"):
                logger.info(f"  [Critic] nemotron confirmed finding at {ts}s — restoring")
                flagged["confidence"] = max(flagged.get("confidence", 2), 3)
                validated.append(flagged)
                valid_ts.add(ts)
                critic_result["confidence"] = min(1.0, critic_result.get("confidence", 0.7) + 0.1)

        critic_result["validated_mistakes"] = validated
        return critic_result
