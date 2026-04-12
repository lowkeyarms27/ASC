"""
Planner Agent — produces forward-looking round strategy.

Takes the validated mistakes and statistical trends, then generates a concrete
action plan for the next round: specific setups to run, utility to prioritize,
positions to avoid, and coordinated plays to attempt.

Completes the coaching loop: analysis → diagnosis → action.
"""
import json
import logging
from backend.agents.game_config import get_config
from backend.utils.gemini_client import _extract_json

logger = logging.getLogger(__name__)


class PlannerAgent:
    def __init__(self, client, model="gemini-2.5-flash"):
        self.client = client
        self.model  = model

    def run(self, coaching_result: dict, trend_report: dict | None, context: dict) -> dict | None:
        """
        Generate a concrete next-round action plan.
        Returns a next_round_plan dict, or None on failure.
        """
        game        = context.get("game", "r6siege")
        atk         = context.get("attacking_team", "Attackers")
        defn        = context.get("defending_team", "Defenders")
        winner      = context.get("winner", "Unknown")
        custom_desc = context.get("custom_game_description", "")
        cfg         = get_config(game, custom_desc)

        mistakes    = coaching_result.get("mistakes", [])
        key_takeaway = coaching_result.get("key_takeaway", "")
        loss_reason  = coaching_result.get("loss_reason", "")

        trend_str = ""
        if trend_report:
            trend_str = f"""
STATISTICAL TRENDS (across recent sessions):
Trajectory: {trend_report.get('overall_trajectory', 'unknown')}
Top recurring mistakes: {json.dumps(trend_report.get('top_recurring_mistakes', []))}
Coaching priority: {trend_report.get('coaching_priority', '')}
"""

        prompt = f"""{cfg['coaching_prompt']}

You are the Planner — your job is to turn analysis into a concrete action plan for the NEXT round.
{atk} attacking, {defn} defending. {winner} won the last round.

WHAT WENT WRONG THIS ROUND:
Loss reason: {loss_reason}
Key takeaway: {key_takeaway}
Mistakes: {json.dumps(mistakes, indent=2)}
{trend_str}

Produce a specific, actionable plan for the next round.
Be concrete — name positions, utility timing, coordination calls.
Do NOT give generic advice. Everything must directly address the mistakes above.

Return ONLY valid JSON:
{{
  "priority_fix": "the single most important thing to change in the next round",
  "setup_adjustments": [
    "specific change to opening phase — drone usage, initial positioning, split"
  ],
  "utility_plan": [
    "specific utility piece to use, when, and why it addresses a mistake from this round"
  ],
  "positions_to_avoid": [
    "specific position or angle that was exploited this round — avoid it"
  ],
  "coordinated_plays": [
    "specific coordinated action involving 2+ players that addresses a gap found this round"
  ],
  "if_losing_again": "if the same mistake happens next round, what is the immediate in-game adjustment?"
}}"""

        logger.info("  [Planner] Generating next-round action plan...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt]
        )

        plan = _extract_json(response.text)
        if not plan:
            logger.warning("  [Planner] Could not parse plan")
            return None

        logger.info(f"  [Planner] Plan ready — priority: {plan.get('priority_fix', '')[:80]}")
        return plan
