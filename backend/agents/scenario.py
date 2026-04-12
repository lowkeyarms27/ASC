"""
Scenario Agent — powered by NVIDIA cosmos-predict1-5b + Gemini.

For each critical mistake in the final report, this agent generates
an alternative scenario: what would have happened if the correct decision
was made instead.

Two-layer approach:
  1. cosmos-predict1-5b — physics-aware future-frame prediction from the
     mistake moment, asked to predict the alternative outcome visually.
  2. Gemini fallback — if cosmos is unavailable, Gemini reasons through
     the counterfactual textually based on the event log.

Output is attached to each critical mistake as a 'scenario' field.
"""
import logging
from backend.utils.nvidia_client import predict_scenario
from backend.utils.gemini_client import _extract_json

logger = logging.getLogger(__name__)


class ScenarioAgent:
    def __init__(self, client):
        self.client = client  # Gemini client for fallback

    def run(self, coaching_result: dict, clip_path: str, event_log: dict, context: dict) -> dict:
        """
        Enrich critical mistakes with alternative scenario descriptions.
        Returns coaching_result with 'scenario' added to critical mistakes.
        """
        atk  = context.get("attacking_team", "Attackers")
        defn = context.get("defending_team", "Defenders")
        game = context.get("game", "r6siege")
        gemini_log = event_log.get("gemini_log", "")

        mistakes = coaching_result.get("mistakes", [])
        critical = [m for m in mistakes if m.get("severity") == "critical"]

        if not critical:
            logger.info("  [Scenario] No critical mistakes — skipping")
            return coaching_result

        logger.info(f"  [Scenario] Generating scenarios for {len(critical)} critical mistake(s)...")

        for m in mistakes:
            if m.get("severity") != "critical":
                continue

            ts          = m.get("timestamp", 0)
            description = m.get("description", "")
            alternative = m.get("better_alternative", "")
            category    = m.get("category", "")

            correction_prompt = (
                f"At {ts} seconds in this {game} round, {m.get('team','a player')} made a {category} error. "
                f"Instead of what happened, the correct action was: {alternative}. "
                f"Predict what the next 10 seconds of the round would look like if that correct action was taken."
            )

            # Try cosmos-predict1-5b first
            scenario_text = predict_scenario(clip_path, correction_prompt)

            # Fallback: Gemini textual counterfactual
            if not scenario_text:
                scenario_text = self._gemini_counterfactual(
                    ts, description, alternative, gemini_log, atk, defn
                )

            if scenario_text:
                m["scenario"] = scenario_text
                logger.info(f"  [Scenario] Scenario for t={ts}s: {scenario_text[:80]}...")

        return coaching_result

    def _gemini_counterfactual(
        self, timestamp: int, mistake: str, alternative: str,
        event_log: str, atk: str, defn: str
    ) -> str | None:
        """Gemini text-based counterfactual reasoning when cosmos is unavailable."""
        prompt = (
            f"FACTUAL EVENT LOG:\n{event_log}\n\n"
            f"MISTAKE at {timestamp}s: {mistake}\n"
            f"CORRECT ALTERNATIVE: {alternative}\n\n"
            f"Using the event log as context, describe in 2-3 sentences what would have "
            f"happened next if the correct action had been taken instead. "
            f"Be specific about the tactical consequences — who would have been in danger, "
            f"what positions would have opened up, and how the round outcome might have changed. "
            f"Start with: 'If instead...'"
        )
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"  [Scenario] Gemini counterfactual failed: {e}")
            return None
