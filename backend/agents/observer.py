"""
Observer Agent — generates factual timestamped event logs from video.
Runs Gemini (pure observation) and Pegasus in parallel, and creates a
Gemini context cache so subsequent agents reuse the video tokens cheaply.
"""
import time
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from google.genai import types
from backend.agents.game_config import get_config
from backend.utils.twelvelabs_client import analyze_with_pegasus
from backend.agents.spatial_observer import SpatialObserverAgent

# Hard cap on how long we wait for all parallel sources before proceeding
_TOTAL_TIMEOUT = 90  # seconds

logger = logging.getLogger(__name__)


class ObserverAgent:
    def __init__(self, client, model="gemini-2.5-flash"):
        self.client = client
        self.model = model

    def run(self, clip_path: str, context: dict) -> dict:
        """
        Upload clip, create a context cache, and produce a factual event log.
        Returns: {uploaded_file, cache_name, event_log}
        """
        logger.info("  [Observer] Uploading clip to Gemini Files API...")
        uploaded = self.client.files.upload(file=clip_path, config={"mime_type": "video/mp4"})
        for _ in range(30):
            f = self.client.files.get(name=uploaded.name)
            if f.state.name == "ACTIVE":
                break
            if f.state.name == "FAILED":
                raise RuntimeError("Gemini file upload failed")
            time.sleep(3)
        else:
            raise RuntimeError("Gemini file upload timed out")

        # ── Create context cache (reduces video token cost for all subsequent agents) ──
        cache_name = None
        try:
            cache = self.client.caches.create(
                model=self.model,
                config=types.CreateCachedContentConfig(
                    contents=[
                        types.Content(
                            role="user",
                            parts=[types.Part(
                                file_data=types.FileData(
                                    file_uri=uploaded.uri,
                                    mime_type="video/mp4"
                                )
                            )]
                        )
                    ],
                    ttl="3600s",
                    display_name=f"asc-video-{uploaded.name.split('/')[-1]}",
                )
            )
            cache_name = cache.name
            logger.info(f"  [Observer] Context cache created: {cache_name}")
        except Exception as e:
            logger.warning(f"  [Observer] Context caching unavailable ({e}) — agents will re-process video tokens")

        atk    = context.get("attacking_team", "Attackers")
        defn   = context.get("defending_team", "Defenders")
        winner = context.get("winner", "Unknown")

        spatial_agent = SpatialObserverAgent()

        from backend.ml.yolo_analyzer import analyze_frames
        from backend.ml.whisper_transcriber import transcribe_clip
        from backend.ml.ocr_analyzer import analyze_hud
        from backend.ml.player_tracker import track_players
        from backend.ml.audio_analyzer import analyze_audio_events
        from backend.ml.clip_analyzer import analyze_clip_concepts

        executor = ThreadPoolExecutor(max_workers=9)
        fs = {
            'gemini':  executor.submit(self._gemini_observe, uploaded, atk, defn, winner, cache_name),
            'pegasus': executor.submit(analyze_with_pegasus, clip_path, context),
            'spatial': executor.submit(spatial_agent.run, clip_path, context),
            'yolo':    executor.submit(analyze_frames, clip_path),
            'whisper': executor.submit(transcribe_clip, clip_path),
            'ocr':     executor.submit(analyze_hud, clip_path),
            'tracker': executor.submit(track_players, clip_path),
            'audio':   executor.submit(analyze_audio_events, clip_path),
            'clip':    executor.submit(analyze_clip_concepts, clip_path),
        }

        # Wait up to _TOTAL_TIMEOUT for everything; move on with whatever finished
        concurrent.futures.wait(fs.values(), timeout=_TOTAL_TIMEOUT)
        executor.shutdown(wait=False)

        def _get(key):
            f = fs[key]
            try:
                return f.result(timeout=0) if f.done() and not f.cancelled() else None
            except Exception:
                return None

        gemini_log     = _get('gemini')
        pegasus_result = _get('pegasus')
        spatial_log    = _get('spatial')
        yolo_result    = _get('yolo')
        whisper_result = _get('whisper')
        ocr_result     = _get('ocr')
        tracker_result = _get('tracker')
        audio_result   = _get('audio')
        clip_result    = _get('clip')

        if gemini_log:   logger.info("  [Observer] Gemini observation complete")
        else:            logger.warning("  [Observer] Gemini observation missing")
        if pegasus_result: logger.info("  [Observer] Pegasus observation complete")
        else:              logger.warning("  [Observer] Pegasus skipped/failed")
        if spatial_log:  logger.info("  [Observer] Spatial analysis complete")
        if yolo_result:  logger.info(f"  [Observer] YOLO complete — {len(yolo_result.get('frames', []))} frames")
        if whisper_result: logger.info(f"  [Observer] Whisper complete — {len(whisper_result.get('segments', []))} segment(s)")
        if ocr_result:   logger.info(f"  [Observer] OCR complete — {ocr_result.get('summary', '')[:60]}")
        if tracker_result: logger.info(f"  [Observer] Tracker complete — {tracker_result.get('player_count', 0)} entities")
        if audio_result: logger.info(f"  [Observer] Audio complete — {audio_result.get('total_spikes', 0)} events")
        if clip_result:  logger.info(f"  [Observer] CLIP complete — {clip_result.get('summary', '')[:60]}")

        # Build YOLO summary string for agents
        yolo_summary = ""
        if yolo_result and yolo_result.get("frames"):
            hints = yolo_result.get("event_hints", [])
            peak  = yolo_result.get("peak_player_count", 0)
            yolo_summary = (
                f"Peak players detected in single frame: {peak}\n"
                + ("\n".join(f"- {h}" for h in hints) if hints else "- No notable patterns detected")
            )

        # Build Whisper summary string for agents
        whisper_summary = ""
        if whisper_result and whisper_result.get("available"):
            transcript = whisper_result.get("transcript", "")
            lang       = whisper_result.get("language", "")
            whisper_summary = f"[Language: {lang}]\n{transcript}" if transcript else ""

        event_log = {
            "gemini_log":         gemini_log or "",
            "pegasus_summary":    pegasus_result.get("summary", "") if isinstance(pegasus_result, dict) else "",
            "pegasus_mistakes":   pegasus_result.get("mistakes", []) if isinstance(pegasus_result, dict) else [],
            "spatial_log":        spatial_log or "",
            "yolo_summary":       yolo_summary,
            "yolo_frames":        yolo_result.get("frames", []) if yolo_result else [],
            "whisper_transcript": whisper_summary,
            "ocr_summary":        ocr_result.get("summary", "") if ocr_result else "",
            "ocr_kills":          ocr_result.get("kills", []) if ocr_result else [],
            "ocr_scores":         ocr_result.get("scores", []) if ocr_result else [],
            "tracker_summary":    tracker_result.get("summary", "") if tracker_result else "",
            "tracker_events":     tracker_result.get("movement_events", []) if tracker_result else [],
            "audio_summary":      audio_result.get("summary", "") if audio_result else "",
            "audio_events":       audio_result.get("events", []) if audio_result else [],
            "clip_summary":       clip_result.get("summary", "") if clip_result else "",
            "clip_concepts":      clip_result.get("frame_concepts", []) if clip_result else [],
            "clip_actions":       clip_result.get("dominant_actions", []) if clip_result else [],
            "attacker":           atk,
            "defender":           defn,
            "winner":             winner,
        }
        logger.info(
            f"  [Observer] Event log ready — Gemini: {len(event_log['gemini_log'])} chars | "
            f"Pegasus: {len(event_log['pegasus_mistakes'])} mistakes | "
            f"YOLO: {len(event_log['yolo_frames'])} frames | "
            f"Whisper: {len(event_log['whisper_transcript'])} chars | "
            f"OCR: {len(event_log['ocr_kills'])} kills | "
            f"Tracker: {tracker_result.get('player_count', 0) if tracker_result else 0} entities | "
            f"Audio: {audio_result.get('total_spikes', 0) if audio_result else 0} events | "
            f"CLIP: {len(event_log['clip_concepts'])} frames | "
            f"Cache: {'yes' if cache_name else 'no'}"
        )

        return {"uploaded_file": uploaded, "cache_name": cache_name, "event_log": event_log}

    def _gemini_observe(self, uploaded_file, atk: str, defn: str, winner: str,
                        cache_name: str | None) -> str:
        """Pure factual observation — no tactics, no blame, only what happened."""
        prompt = (
            f"{atk} are attacking, {defn} are defending. {winner} won.\n\n"
            f"Watch the entire clip and produce ONLY a factual timestamped event log.\n"
            f"Include:\n"
            f"- Every elimination: [Xs] who died (attacker/defender), by what method, from which direction\n"
            f"- Every utility or ability used: [Xs] what was used, where, what it hit or missed\n"
            f"- Significant player movements or position changes: [Xs] what happened\n\n"
            f"Rules:\n"
            f"- Do NOT interpret tactics or explain why something was good or bad\n"
            f"- Do NOT assign blame or make coaching points\n"
            f"- Only state what you directly observe\n"
            f"- Use format: [Xs] <factual description>"
        )
        cfg = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=1024)
        )
        if cache_name:
            cfg = types.GenerateContentConfig(
                cached_content=cache_name,
                thinking_config=types.ThinkingConfig(thinking_budget=1024)
            )
            response = self.client.models.generate_content(
                model=self.model, contents=[prompt], config=cfg
            )
        else:
            response = self.client.models.generate_content(
                model=self.model, contents=[uploaded_file, prompt], config=cfg
            )
        return response.text
