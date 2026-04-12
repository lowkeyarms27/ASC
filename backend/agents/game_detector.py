"""
Game Detector — identifies the game/sport from a clip frame using Gemini vision.
Falls back to filename heuristic if vision detection fails.
"""
import base64
import logging
from backend.agents.game_config import GAME_CONFIGS, detect_game
from backend.utils.video_processor import extract_frame_b64

logger = logging.getLogger(__name__)

_KNOWN_SLUGS = list(GAME_CONFIGS.keys())


def detect_game_from_clip(clip_path: str, client) -> str:
    """
    Returns a game slug (from GAME_CONFIGS) or 'custom'.
    Tries Gemini vision on a frame at ~5s, then falls back to filename heuristic.
    """
    try:
        frame_b64 = extract_frame_b64(clip_path, timestamp=5.0)
        if frame_b64:
            slug = _classify_frame(frame_b64, client)
            if slug:
                logger.info(f"  [GameDetector] Vision detected: {slug}")
                return slug
    except Exception as e:
        logger.warning(f"  [GameDetector] Vision failed: {e}")

    import os
    slug = detect_game(os.path.basename(clip_path))
    logger.info(f"  [GameDetector] Filename heuristic: {slug}")
    return slug


def _classify_frame(frame_b64: str, client) -> str | None:
    """Send a single JPEG frame to Gemini and return the game slug."""
    from google.genai import types

    slugs = ", ".join(_KNOWN_SLUGS)
    prompt = (
        "Look at this game screenshot. "
        f"Which of these games or sports is shown? Choose exactly one:\n{slugs}\n\n"
        "Reply with ONLY the slug (e.g. 'r6siege'). "
        "If none match, reply with 'custom'. No other text."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=base64.b64decode(frame_b64),
                mime_type="image/jpeg",
            ),
            prompt,
        ],
    )

    text = (response.text or "").strip().lower().split()[0] if response.text else ""
    if text in _KNOWN_SLUGS:
        return text
    if text == "custom":
        return "custom"
    return None
