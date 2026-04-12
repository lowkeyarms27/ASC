"""
Embedder — uses sentence-transformers (PyTorch) to embed mistake
descriptions into dense vectors for semantic similarity search.

Model: all-MiniLM-L6-v2 (~90 MB, fast CPU inference)
Enables: "find all past rounds where the same type of mistake happened"
         and clustering of recurring error patterns.
"""
import logging
import json

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("  [Embedder] Loading all-MiniLM-L6-v2...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("  [Embedder] Model ready.")
    return _model


def embed_text(text: str) -> list[float] | None:
    """Return a 384-dim embedding vector for a text string."""
    if not text or not text.strip():
        return None
    try:
        model = _get_model()
        vec = model.encode(text, show_progress_bar=False)
        return vec.tolist()
    except Exception as e:
        logger.warning(f"  [Embedder] embed_text failed: {e}")
        return None


def embed_mistake(mistake: dict) -> list[float] | None:
    """
    Embed a mistake dict using description + category + severity
    for richer semantic representation.
    """
    parts = [
        mistake.get("description", ""),
        mistake.get("category", ""),
        mistake.get("severity", ""),
        mistake.get("better_alternative", ""),
    ]
    text = " | ".join(p for p in parts if p)
    return embed_text(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    import math
    dot  = sum(x * y for x, y in zip(a, b))
    na   = math.sqrt(sum(x * x for x in a))
    nb   = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def find_similar_mistakes(query: str, candidates: list[dict],
                           top_k: int = 5, threshold: float = 0.55) -> list[dict]:
    """
    Given a query string and a list of mistake dicts (each with an
    'embedding' key as a JSON-serialised list), return the top_k most
    similar mistakes above threshold.
    """
    q_vec = embed_text(query)
    if not q_vec:
        return []

    scored = []
    for m in candidates:
        raw = m.get("embedding")
        if not raw:
            continue
        try:
            m_vec = json.loads(raw) if isinstance(raw, str) else raw
            score = cosine_similarity(q_vec, m_vec)
            if score >= threshold:
                scored.append({**m, "_similarity": round(score, 3)})
        except Exception:
            continue

    scored.sort(key=lambda x: x["_similarity"], reverse=True)
    return scored[:top_k]
