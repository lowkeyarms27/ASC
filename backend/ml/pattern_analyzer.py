"""
Pattern Analyzer — clusters stored mistake embeddings to surface recurring tactical
patterns and anomalies. Uses scikit-learn K-Means and DBSCAN.
"""
import logging
import json
import numpy as np

logger = logging.getLogger(__name__)


def analyze_mistake_patterns(mistakes: list, n_clusters: int = 5) -> dict:
    """
    Cluster mistakes by embedding similarity.
    Returns: cluster summaries, anomalies, silhouette score.
    """
    try:
        from sklearn.cluster import KMeans, DBSCAN
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score
    except ImportError:
        logger.warning("scikit-learn not installed — pattern analysis unavailable")
        return {"clusters": [], "anomalies": [], "total_analyzed": 0}

    # Parse embeddings
    embedded = []
    for m in mistakes:
        raw = m.get("embedding")
        if not raw:
            continue
        try:
            vec = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(vec, list) and len(vec) > 10:
                embedded.append((m, np.array(vec, dtype=np.float32)))
        except Exception:
            continue

    if len(embedded) < 3:
        return {"clusters": [], "anomalies": [], "total_analyzed": len(embedded)}

    vectors = np.stack([v for _, v in embedded])

    # ── K-Means ──────────────────────────────────────────────────────────────
    k = min(n_clusters, len(embedded))
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    sil_score = None
    if k > 1 and len(embedded) > k:
        try:
            sil_score = round(float(silhouette_score(vectors, labels)), 3)
        except Exception:
            pass

    clusters = []
    for c in range(k):
        indices = [i for i, l in enumerate(labels) if l == c]
        cluster_mistakes = [embedded[i][0] for i in indices]

        categories = [m.get("category", "unknown") for m in cluster_mistakes]
        severities = [m.get("severity", "unknown") for m in cluster_mistakes]

        cat_counts: dict = {}
        for cat in categories:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        top_cat = max(cat_counts, key=cat_counts.get)

        clusters.append({
            "id":                   c,
            "size":                 len(cluster_mistakes),
            "dominant_category":    top_cat,
            "category_breakdown":   cat_counts,
            "severity_breakdown":   {s: severities.count(s) for s in set(severities)},
            "examples":             [m.get("description", "")[:120] for m in cluster_mistakes[:3]],
        })

    clusters.sort(key=lambda x: x["size"], reverse=True)

    # ── DBSCAN anomaly detection ──────────────────────────────────────────────
    scaler = StandardScaler()
    scaled = scaler.fit_transform(vectors)
    db_labels = DBSCAN(eps=0.8, min_samples=2).fit_predict(scaled)

    anomalies = []
    for i in np.where(db_labels == -1)[0][:8]:
        m = embedded[i][0]
        anomalies.append({
            "description": m.get("description", "")[:120],
            "category":    m.get("category", "unknown"),
            "severity":    m.get("severity", "unknown"),
            "session_id":  m.get("session_id"),
        })

    return {
        "clusters":        clusters,
        "anomalies":       anomalies,
        "total_analyzed":  len(embedded),
        "silhouette_score": sil_score,
    }
