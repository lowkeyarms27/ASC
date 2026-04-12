from backend.agents.searcher import search
from backend.agents.game_config import get_config


def _dedupe(clips: list[dict], min_gap: float) -> list[dict]:
    """Keep only clips at least min_gap seconds after the previous accepted one."""
    if not clips:
        return []
    accepted = [clips[0]]
    for c in clips[1:]:
        if c["start"] - accepted[-1]["start"] >= min_gap:
            accepted.append(c)
    return accepted


def _safe_search(index_id, video_id, query, threshold="high"):
    try:
        return search(index_id, video_id, query, threshold=threshold)
    except Exception as e:
        print(f"  Search failed ({e})")
        return []


def detect_rounds(index_id: str, video_id: str, video_duration: float, start_offset: int, game: str) -> list[dict]:
    cfg = get_config(game)
    min_gap = cfg["min_gap_between_rounds"]
    min_round = cfg["min_round_seconds"]
    max_round = cfg["max_round_seconds"]

    # Search for round starts — try each query, merge results
    print("Searching for round starts...")
    raw_starts = []
    for q in cfg["round_start_queries"]:
        raw_starts += _safe_search(index_id, video_id, q, threshold="high")
    raw_starts.sort(key=lambda x: x["start"])
    print(f"  Found {len(raw_starts)} candidates")

    print("Searching for round ends...")
    raw_ends = []
    for q in cfg["round_end_queries"]:
        raw_ends += _safe_search(index_id, video_id, q, threshold="high")
    raw_ends.sort(key=lambda x: x["start"])
    print(f"  Found {len(raw_ends)} candidates")

    # Search for key events (plants, wipes, goals, etc.)
    key_events = {}
    for event_name, query in cfg["key_event_queries"].items():
        print(f"Searching for {event_name} events...")
        hits = _safe_search(index_id, video_id, query, threshold="medium")
        key_events[event_name] = _dedupe(sorted(hits, key=lambda x: x["start"]), min_gap=10.0)
        print(f"  Found {len(key_events[event_name])} {event_name} events")

    starts = _dedupe(raw_starts, min_gap=min_gap)
    ends = _dedupe(raw_ends, min_gap=min_gap)
    print(f"  After dedup: {len(starts)} starts, {len(ends)} ends")

    # Pair each start with next valid end
    rounds = []
    used_ends = set()
    for s in starts:
        round_start = s["end"]
        for j, e in enumerate(ends):
            if j in used_ends:
                continue
            if e["start"] <= round_start + min_round:
                continue
            if e["start"] - round_start > max_round:
                break
            used_ends.add(j)

            round_end = e["start"]
            round_events = {}
            for event_name, hits in key_events.items():
                for h in hits:
                    if round_start <= h["start"] <= round_end:
                        round_events[event_name] = int(h["start"]) + start_offset
                        break

            rounds.append({
                "round_number": len(rounds) + 1,
                "start_time": int(round_start) + start_offset,
                "end_time": int(round_end) + start_offset,
                "plant_timestamp": round_events.get("plant"),
                "attacking_team": None,
                "defending_team": None,
                "winner": None,
                "events": round_events,
            })
            break

    print(f"  Built {len(rounds)} rounds from search")

    if not rounds:
        print("  No rounds found — using time-based fallback")
        chunk = min_round
        t = 0
        while t + chunk < video_duration:
            rounds.append({
                "round_number": len(rounds) + 1,
                "start_time": int(t) + start_offset,
                "end_time": int(t + chunk) + start_offset,
                "plant_timestamp": None,
                "attacking_team": None,
                "defending_team": None,
                "winner": None,
                "events": {},
            })
            t += chunk

    return rounds
