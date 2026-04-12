"""
Statistician Agent — surfaces patterns across sessions over time.

Queries the DB for historical sessions involving the same teams and game,
identifies recurring mistake categories, win/loss trends, improvement or
regression across rounds, persistent cross-session patterns (deduplication),
and builds opponent profiles.
"""
import json
import logging
from backend.database import get_connection, get_opponent_profile
from backend.utils.gemini_client import _extract_json

logger = logging.getLogger(__name__)

MIN_SESSIONS_FOR_TRENDS  = 3
PERSISTENT_PATTERN_COUNT = 3   # mistake category must appear this many times to be "persistent"


class StatisticianAgent:
    def __init__(self, client, model="gemini-2.5-flash"):
        self.client = client
        self.model  = model

    def run(self, context: dict, current_result: dict) -> dict | None:
        game  = context.get("game", "r6siege")
        atk   = context.get("attacking_team", "Attackers")
        defn  = context.get("defending_team", "Defenders")

        history = self._fetch_history(game, atk, defn)
        if len(history["sessions"]) < MIN_SESSIONS_FOR_TRENDS:
            logger.info(f"  [Statistician] {len(history['sessions'])} session(s) — "
                        f"need {MIN_SESSIONS_FOR_TRENDS} for trends. Skipping.")
            return None

        current_mistakes = current_result.get("mistakes", [])
        category_counts  = self._count_categories(history["mistakes"])
        win_rate         = self._win_rate(history["sessions"], atk)
        persistent       = self._detect_persistent_patterns(history["mistakes"], current_mistakes)

        # Opponent profile for the defending team (who the attackers need to beat)
        opp_profile = get_opponent_profile(game, defn)

        prompt = f"""You are a statistical analyst for an esports coaching platform.
Game: {game} | Attackers: {atk} | Defenders: {defn}

HISTORICAL DATA ({len(history['sessions'])} past sessions):
Win rate for {atk} attacking: {win_rate:.0%}

Mistake category frequency across all past rounds:
{json.dumps(category_counts, indent=2)}

Sample of recent mistakes (last 20):
{json.dumps(history['mistakes'][:20], indent=2)}

PERSISTENT PATTERNS (same category appearing {PERSISTENT_PATTERN_COUNT}+ times):
{json.dumps(persistent, indent=2)}

OPPONENT PROFILE ({defn}):
{json.dumps(opp_profile, indent=2) if opp_profile else "(no opponent history)"}

CURRENT ROUND MISTAKES:
{json.dumps(current_mistakes, indent=2)}

Produce a statistical trend report. Identify:
1. Recurring patterns — what mistakes keep appearing session after session?
2. Improvement areas — any categories appearing less frequently recently?
3. Regression areas — any categories getting worse?
4. Whether current round mistakes are typical or unusual for this team
5. Overall trajectory — is performance improving, declining, or flat?
6. Opponent tendencies — what patterns does {defn} repeatedly show that {atk} can exploit?

Return ONLY valid JSON:
{{
  "sessions_analysed": {len(history['sessions'])},
  "win_rate_attacking": {round(win_rate, 2)},
  "top_recurring_mistakes": [
    {{"category": "...", "frequency": <int>, "insight": "..."}}
  ],
  "persistent_patterns": [
    {{"category": "...", "occurrences": <int>, "urgency": "high|medium", "note": "..."}}
  ],
  "improving":  ["categories showing fewer recent occurrences"],
  "regressing": ["categories showing more recent occurrences"],
  "current_round_vs_history": "is this round typical, worse, or better than average?",
  "overall_trajectory": "improving | declining | flat",
  "coaching_priority": "the single most important pattern the coach should address",
  "opponent_exploits": ["specific tendencies of {defn} that {atk} should target next round"]
}}"""

        logger.info(f"  [Statistician] Analysing {len(history['sessions'])} sessions, "
                    f"{len(history['mistakes'])} mistakes, "
                    f"{len(persistent)} persistent patterns...")
        response = self.client.models.generate_content(
            model=self.model, contents=[prompt]
        )

        report = _extract_json(response.text)
        if not report:
            logger.warning("  [Statistician] Could not parse trend report")
            return None

        logger.info(f"  [Statistician] Trajectory: {report.get('overall_trajectory', '?')}")
        return report

    def _fetch_history(self, game: str, atk: str, defn: str) -> dict:
        with get_connection() as conn:
            sessions = conn.execute(
                """SELECT id, attacking_team, defending_team, winner, created_at
                   FROM sessions
                   WHERE game = ? AND status = 'complete'
                   AND (attacking_team = ? OR defending_team = ? OR attacking_team = ? OR defending_team = ?)
                   ORDER BY id DESC LIMIT 30""",
                (game, atk, atk, defn, defn)
            ).fetchall()

            session_ids = [s["id"] for s in sessions]
            mistakes = []
            if session_ids:
                placeholders = ",".join("?" * len(session_ids))
                mistakes = conn.execute(
                    f"""SELECT m.category, m.severity, m.description, m.confidence,
                               s.attacking_team, s.defending_team, s.winner, s.created_at, s.id as session_id
                        FROM mistakes m JOIN sessions s ON m.session_id = s.id
                        WHERE m.session_id IN ({placeholders})
                        ORDER BY s.id DESC""",
                    session_ids
                ).fetchall()

        return {
            "sessions": [dict(s) for s in sessions],
            "mistakes":  [dict(m) for m in mistakes],
        }

    def _count_categories(self, mistakes: list) -> dict:
        counts: dict = {}
        for m in mistakes:
            cat = m.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def _win_rate(self, sessions: list, atk: str) -> float:
        atk_sessions = [s for s in sessions if s.get("attacking_team") == atk]
        if not atk_sessions:
            return 0.0
        wins = sum(1 for s in atk_sessions if s.get("winner") == atk)
        return wins / len(atk_sessions)

    def _detect_persistent_patterns(self, history_mistakes: list,
                                     current_mistakes: list) -> list:
        """
        Find mistake categories in the current round that also appeared
        PERSISTENT_PATTERN_COUNT or more times in history — these are not
        one-off errors but systemic issues requiring focused coaching.
        """
        hist_cats: dict = {}
        for m in history_mistakes:
            key = m.get("category", "unknown")
            hist_cats[key] = hist_cats.get(key, 0) + 1

        persistent = []
        seen = set()
        for m in current_mistakes:
            cat   = m.get("category", "unknown")
            count = hist_cats.get(cat, 0)
            if count >= PERSISTENT_PATTERN_COUNT and cat not in seen:
                seen.add(cat)
                persistent.append({
                    "category":   cat,
                    "occurrences": count,
                    "urgency":    "high" if count >= PERSISTENT_PATTERN_COUNT * 2 else "medium",
                })
        return persistent
