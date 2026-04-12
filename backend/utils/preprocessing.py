import os
import re
import json
import subprocess


def get_duration(video_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", video_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def detect_breaks(video_path: str, min_break_seconds: float = 120.0) -> list[tuple]:
    """
    Returns list of (start, end) for black-frame segments longer than min_break_seconds.
    Samples at 1fps for speed on long files.
    """
    result = subprocess.run(
        ["ffmpeg", "-i", video_path,
         "-vf", f"fps=1,blackdetect=d={min_break_seconds}:pix_th=0.10",
         "-f", "null", "-"],
        capture_output=True, text=True
    )
    breaks = []
    for line in result.stderr.split("\n"):
        if "black_start" not in line:
            continue
        m_start = re.search(r"black_start:([\d.]+)", line)
        m_end = re.search(r"black_end:([\d.]+)", line)
        if m_start and m_end:
            breaks.append((float(m_start.group(1)), float(m_end.group(1))))
    return breaks


def extract_map_segments(video_path: str, output_dir: str) -> list[dict]:
    """
    Detects broadcast breaks, extracts the 3 longest content segments as map files.
    Returns list of {path, start_offset, map_number}.
    """
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    meta_path = os.path.join(output_dir, f"{base}_maps_meta.json")
    existing = [os.path.join(output_dir, f"{base}_map{i}.mp4") for i in range(1, 4)]
    if all(os.path.exists(p) for p in existing) and os.path.exists(meta_path):
        with open(meta_path) as f:
            offsets = json.load(f)
        print("All 3 map segments already exist, skipping blackdetect.")
        return [
            {"path": existing[i], "start_offset": offsets[i], "map_number": i + 1}
            for i in range(3)
        ]

    total = get_duration(video_path)
    breaks = detect_breaks(video_path, min_break_seconds=120.0)

    # Build content intervals (gaps between breaks)
    boundaries = [0.0] + [t for b in breaks for t in b] + [total]
    boundaries.sort()

    content_segments = []
    for i in range(0, len(boundaries) - 1, 2):
        start = boundaries[i]
        end = boundaries[i + 1]
        dur = end - start
        if dur > 60:  # ignore very short content clips
            content_segments.append((start, end, dur))

    # If no breaks found, split into 3 equal thirds
    if not content_segments or len(content_segments) < 2:
        third = total / 3
        content_segments = [
            (0, third, third),
            (third, third * 2, third),
            (third * 2, total, total - third * 2),
        ]

    # Take 3 longest segments (the actual maps)
    content_segments.sort(key=lambda x: x[2], reverse=True)
    map_segments = sorted(content_segments[:3], key=lambda x: x[0])

    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    meta_path = os.path.join(output_dir, f"{base}_maps_meta.json")
    results = []

    for i, (start, end, dur) in enumerate(map_segments):
        out_path = os.path.join(output_dir, f"{base}_map{i + 1}.mp4")
        if not os.path.exists(out_path):
            print(f"Extracting map {i + 1} ({start:.0f}s–{end:.0f}s, {dur:.0f}s)...")
            subprocess.run([
                "ffmpeg", "-y",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(end - start),
                "-c", "copy",
                out_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        results.append({
            "path": out_path,
            "start_offset": int(start),
            "map_number": i + 1
        })

    with open(meta_path, "w") as f:
        json.dump([r["start_offset"] for r in results], f)

    return results
