"""
Groq Vision client — extracts frames directly from the source VOD at absolute
timestamps and sends them to llama-4-scout for visual analysis.
"""
import os
import base64
import subprocess
import json
import re
import time
import tempfile
import requests


GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_FRAMES = 4  # Groq rejects requests with more images


def _extract_frame(video_path: str, timestamp_s: int) -> str | None:
    """Extract a single frame from video_path at timestamp_s. Returns base64 or None."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        frame_path = f.name

    subprocess.run([
        "ffmpeg", "-y", "-ss", str(timestamp_s), "-i", video_path,
        "-vframes", "1", "-q:v", "4", "-vf", "scale=480:-1",
        frame_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
        with open(frame_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        os.unlink(frame_path)
        return b64

    if os.path.exists(frame_path):
        os.unlink(frame_path)
    return None


def _extract_json(text: str):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'```(?:json)?\s*([\[{][\s\S]*?[\]}])\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    match = re.search(r'(\{[\s\S]*\})', text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return None


def analyze_round(video_path: str, round_start: int, round_end: int, prompt_context: str) -> dict | None:
    """
    Extract MAX_FRAMES evenly distributed frames directly from video_path at
    absolute timestamps within [round_start, round_end], send to Groq Vision.

    Returns {loss_reason, mistakes: [{team, description, timestamp, better_alternative}]}
    where timestamp is an absolute VOD timestamp matching the labeled frame.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    duration = round_end - round_start
    # Sample at 20%, 40%, 60%, 80% of the round — absolute VOD timestamps
    frame_timestamps = [
        round_start + int(duration * (i + 1) / (MAX_FRAMES + 1))
        for i in range(MAX_FRAMES)
    ]

    frames = []
    for t in frame_timestamps:
        b64 = _extract_frame(video_path, t)
        if b64:
            frames.append({"timestamp_s": t, "image_b64": b64})

    if not frames:
        return None

    print(f"    Extracted {len(frames)} frames at {[f['timestamp_s'] for f in frames]}, sending to Groq Vision...")

    content = [
        {
            "type": "text",
            "text": (
                f"{prompt_context}\n\n"
                f"Below are {len(frames)} frames from this round, evenly distributed. "
                f"Each frame is labeled with its ABSOLUTE timestamp in the VOD (in seconds).\n\n"
                f"Analyze the gameplay. Identify the 2-3 biggest tactical mistakes.\n"
                f"For each mistake, use the EXACT TIMESTAMP LABEL of the frame where it is most visible.\n\n"
                f"Return ONLY valid JSON:\n"
                '{{"loss_reason": "one sentence", "mistakes": ['
                '{{"team": "Attackers or Defenders", '
                '"description": "what went wrong", '
                '"timestamp_s": <int — must match one of the frame timestamp labels>, '
                '"better_alternative": "what should have been done"'
                '}}]}}'
            )
        }
    ]

    for frame in frames:
        ts = frame["timestamp_s"]
        content.append({"type": "text", "text": f"--- Frame at {ts}s ---"})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{frame['image_b64']}"}
        })

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_VISION_MODEL,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "max_tokens": 1000
    }

    for attempt in range(4):
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload
        )
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 20)) + 2
            print(f"    Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break

    raw = resp.json()["choices"][0]["message"]["content"]
    print(f"    Groq Vision raw: {raw[:300]}")

    result = _extract_json(raw)
    if not result or "mistakes" not in result:
        return None

    # timestamps in the response are already absolute VOD timestamps
    valid_ts = {f["timestamp_s"] for f in frames}
    for m in result["mistakes"]:
        ts = m.pop("timestamp_s", None)
        # Clamp to nearest valid frame timestamp if model went off-label
        if ts not in valid_ts:
            ts = min(valid_ts, key=lambda x: abs(x - (ts or round_start)))
        m["timestamp"] = ts

    return result
