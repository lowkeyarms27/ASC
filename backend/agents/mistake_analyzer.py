import os
from backend.utils.gemini_client import analyze_clip
from backend.agents.game_config import get_config


def analyze_mistakes(round_data: dict, game: str, clip_path: str = None,
                     team1: dict | None = None, team2: dict | None = None) -> dict:
    cfg = get_config(game)
    start = round_data.get("start_time", 0)
    end = round_data.get("end_time", 0)
    duration = end - start
    round_num = round_data.get("round_number", "?")
    plant_ts = round_data.get("plant_timestamp")
    events = round_data.get("events", {})
    atk = round_data.get("attacking_team", "Attackers")
    defn = round_data.get("defending_team", "Defenders")
    winner = round_data.get("winner", "Unknown")

    if not clip_path or not os.path.exists(clip_path):
        print(f"  Round {round_num}: no clip available")
        return {"loss_reason": "No clip available", "mistakes": []}

    roster_text = (
        f"Do NOT use individual player names or operator names in your analysis. "
        f"Refer to players only as '{atk} attacker' or '{defn} defender'. "
        f"Focus on the tactical decision, the position, and the mistake — not who specifically made it."
    )

    event_lines = []
    if plant_ts:
        event_lines.append(f"Defuser planted at {plant_ts - start:.0f}s into this clip.")
    for name, ts in events.items():
        event_lines.append(f"{name.replace('_',' ').capitalize()} at {ts - start:.0f}s into this clip.")
    events_text = "\n".join(event_lines) if event_lines else "No pre-detected events."

    prompt_context = (
        f"{cfg['coaching_prompt']}\n\n"
        f"{roster_text}\n\n"
        f"Round {round_num} — {atk} attacking, {defn} defending. {winner} won. "
        f"{duration:.0f} seconds long.\n"
        f"Known events: {events_text}"
    )

    print(f"  Round {round_num}: sending {duration:.0f}s clip to Gemini...")
    try:
        result = analyze_clip(clip_path, int(start), prompt_context)
        if result:
            print(f"  Round {round_num}: got {len(result.get('mistakes', []))} mistakes")
            return result
    except Exception as e:
        print(f"  Round {round_num}: Gemini failed — {e}")

    return {"loss_reason": "Analysis unavailable", "mistakes": []}
