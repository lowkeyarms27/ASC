import os
import json
import re
from backend.agents.indexer import get_client

def _extract_json(text: str):
    """Extract JSON object or array from text that may contain prose or markdown."""
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    # Strip markdown code fences
    match = re.search(r'```(?:json)?\s*([\[{].*?[\]}])\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    # Find first JSON array or object in the text
    match = re.search(r'(\[[\s\S]*?\]|\{[\s\S]*?\})', text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return None

def detect_rounds(index_id: str, video_parts: list[dict]) -> list[dict]:
    """video_parts is list of {video_id, start_offset}."""
    client = get_client()
    all_rounds = []

    for part in video_parts:
        video_id = part["video_id"]
        offset = part["start_offset"]
        prompt = (
            f"Analyze this match segment (starting at {offset}s into the full match). "
            "Identify every round played in this segment. "
            "For each round return: round_number (int), attacking_team (string), defending_team (string), "
            f"start_time (int seconds, relative to full video so add {offset} to your timestamps), "
            f"end_time (int seconds, relative to full video), winner (string). "
            "ONLY return a valid JSON array, no explanation."
        )
        try:
            res = client.generate.text(video_id=video_id, prompt=prompt, stream=False)
            data = getattr(res, 'data', getattr(res, 'text', ''))
            result = _extract_json(data)
            if isinstance(result, list):
                all_rounds.extend(result)
            else:
                print(f"Failed to parse rounds JSON for part offset={offset}. Raw: {data[:300]}")
        except Exception as e:
            print(f"Generate text failed: {e}")

    # Deduplicate by round_number, keep first
    seen = set()
    unique = []
    for r in sorted(all_rounds, key=lambda x: x.get("round_number", 0)):
        rn = r.get("round_number")
        if rn not in seen:
            seen.add(rn)
            unique.append(r)
    return unique

def _find_part_for_time(video_parts: list[dict], timestamp: int) -> dict:
    """Return the video part that covers the given absolute timestamp."""
    for i, part in enumerate(video_parts):
        next_offset = video_parts[i + 1]["start_offset"] if i + 1 < len(video_parts) else float("inf")
        if part["start_offset"] <= timestamp < next_offset:
            return part
    return video_parts[-1]

def analyze_plant(index_id: str, video_parts: list[dict], round_start: int, round_end: int) -> dict:
    client = get_client()
    part = _find_part_for_time(video_parts, round_start)
    video_id = part["video_id"]
    offset = part["start_offset"]
    local_start = round_start - offset
    local_end = round_end - offset

    prompt = (
        f"In this round (local timestamps {local_start}s to {local_end}s in this video segment), "
        "was the defuser planted? "
        "If yes: at what local timestamp (seconds in this segment), how many seconds were remaining on the timer, "
        "was the timing good or rushed and why? Return ONLY JSON: "
        "{\"planted\": bool, \"plant_timestamp\": int or null, \"seconds_remaining\": int or null, \"timing_assessment\": string}"
    )
    
    try:
        res = client.generate.text(video_id=video_id, prompt=prompt, stream=False)
        data = getattr(res, 'data', getattr(res, 'text', ''))
        result = _extract_json(data)
        if isinstance(result, dict):
            # Convert local timestamp back to full video timestamp
            if result.get("plant_timestamp") is not None:
                result["plant_timestamp"] = result["plant_timestamp"] + offset
            return result
        print(f"Failed to parse plant JSON. Raw: {data[:300]}")
    except Exception as e:
        print(f"Generate text failed: {e}")

    return {
        "planted": False,
        "plant_timestamp": None,
        "seconds_remaining": None,
        "timing_assessment": "Could not determine"
    }
