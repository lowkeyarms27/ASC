"""
Shared tools available to agents during analysis.
These are callable actions — not just LLM inference.
"""
from google.genai import types


def examine_clip_at_timestamp(
    uploaded_file, timestamp: int, question: str, client,
    cache_name: str | None = None
) -> str:
    """
    Re-examine a specific moment in an already-uploaded clip.
    Uses cached content when available to avoid re-processing video tokens.
    """
    prompt = (
        f"Focus ONLY on the moment at approximately {timestamp} seconds in this clip.\n"
        f"Question: {question}\n"
        f"Answer factually with only what you can directly observe at that timestamp. "
        f"If you cannot clearly see the answer, say so explicitly."
    )
    if cache_name:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(cached_content=cache_name)
        )
    else:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt]
        )
    return response.text.strip()


def search_historical_rounds(game: str, category: str, limit: int = 2) -> list[dict]:
    """
    Query the database for similar historical mistakes in the same category.
    Used by Coach to enrich coaching advice with real past examples.
    """
    from backend.database import get_connection
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT m.category, m.severity, m.description, m.better_alternative
               FROM mistakes m
               JOIN sessions s ON m.session_id = s.id
               WHERE s.game = ? AND m.category = ? AND s.status = 'complete' AND s.rating >= 3
               ORDER BY RANDOM()
               LIMIT ?""",
            (game, category, limit)
        ).fetchall()
    return [dict(r) for r in rows]
