import os
from twelvelabs import TwelveLabs

def get_client() -> TwelveLabs:
    api_key = os.environ.get("TWELVELABS_API_KEY")
    if not api_key:
        raise ValueError("TWELVELABS_API_KEY environment variable is not set")
    return TwelveLabs(api_key=api_key)

def ensure_index(index_name: str) -> str:
    client = get_client()
    indexes = client.index.list()
    for idx in indexes:
        if idx.name == index_name:
            return idx.id

    print(f"Creating new Twelve Labs index: {index_name}")
    idx = client.index.create(
        name=index_name,
        models=[
            {"name": "marengo3.0", "options": ["visual", "audio"]},
            {"name": "pegasus1.2", "options": ["visual", "audio"]}
        ],
        addons=["thumbnail"]
    )
    return idx.id

def _get_existing_videos(index_id: str) -> dict:
    client = get_client()
    try:
        videos = client.index.video.list(index_id)
        # Using getattr to be safe with SDK attribute name variations
        return {
            getattr(v.metadata, 'filename', getattr(v, 'filename', '')): v.id
            for v in videos
        }
    except Exception as e:
        print(f"Error fetching existing videos: {e}")
        return {}

def upload_file(index_id: str, file_path: str) -> str:
    client = get_client()
    filename = os.path.basename(file_path)
    print(f"  Uploading {filename} to Twelve Labs...")
    
    # Official SDK create task
    task = client.task.create(index_id=index_id, file=file_path)
    
    # wait_for_done handles polling and rate limits nicely
    def on_progress(t):
        print(f"  Task {t.id}: {t.status}")

    try:
        task.wait_for_done(callback=on_progress)
    except Exception as e:
        print(f"  Wait for task raised exception: {e}")

    if task.status.lower() == "failed":
        raise RuntimeError(f"Indexing failed: {getattr(task, 'error', 'Unknown Error')}")
        
    return task.video_id

def get_or_upload(index_id: str, file_path: str) -> str:
    filename = os.path.basename(file_path)
    existing = _get_existing_videos(index_id)
    if filename in existing and existing[filename]:
        print(f"  Already indexed: {filename}")
        return existing[filename]
    return upload_file(index_id, file_path)
