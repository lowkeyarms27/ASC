import os
from twelvelabs import TwelveLabs

def get_client() -> TwelveLabs:
    api_key = os.environ.get("TWELVELABS_API_KEY")
    if not api_key:
        raise ValueError("TWELVELABS_API_KEY environment variable is not set")
    return TwelveLabs(api_key=api_key)

def search(index_id: str, video_id: str, query: str, threshold: str = "low") -> list[dict]:
    """
    Search for moments in a specific video matching the query using official SDK.
    Returns list of {start, end, score, thumbnail_url} sorted by start time.
    """
    client = get_client()
    
    res = client.search.query(
        index_id=index_id,
        query_text=query,
        search_options=["visual", "audio"],
        filter={"id": [video_id]}
    )

    clips = []
    # res.data contains the clips, and res can be iterated if it handles pagination safely
    try:
        # SDK handles pagination behind the scenes usually, or we just consume data
        data_items = res.data if hasattr(res, 'data') else res
        
        for item in data_items:
            # Depending on SDK version, score/start/end could be attributes
            score = getattr(item, 'score', 0)
            start = getattr(item, 'start', 0)
            end = getattr(item, 'end', 0)
            thumbnail_url = getattr(item, 'thumbnail_url', None)
            
            clips.append({
                "start": float(start),
                "end": float(end),
                "score": float(score),
                "thumbnail_url": thumbnail_url,
            })
    except Exception as e:
        print(f"Error parsing search results: {e}")

    return sorted(clips, key=lambda x: x["start"])
