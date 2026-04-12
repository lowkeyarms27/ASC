import os
import json
import logging
import threading
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.database import (
    create_session, update_session, get_session, save_mistake, get_results,
    list_sessions, save_feedback, get_top_examples, append_agent_log_event, get_agent_log_live,
    semantic_search_mistakes, get_embedded_mistakes,
)
from backend.agents.orchestrator import Orchestrator
from backend.utils.video_processor import extract_clip, get_clip_duration
from backend.utils.pdf_generator import generate_pdf
from backend.config import UPLOADS_DIR, CLIPS_DIR

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES    = 2 * 1024 * 1024 * 1024   # 2 GB
_analysis_semaphore = threading.Semaphore(2)


# ── Background task helpers ───────────────────────────────────────────────────

def process_clip(session_id: int, clip_path: str, context: dict,
                 examples: list = None, webhook_url: str = "",
                 confidence_threshold: float = 0.75):
    try:
        update_session(session_id, status="analysing")
        acquired = _analysis_semaphore.acquire(timeout=300)
        if not acquired:
            update_session(session_id, status="failed",
                           error_message="Server busy — too many analyses running. Please retry.")
            return
        try:
            _run_analysis(session_id, clip_path, context, examples,
                          webhook_url, confidence_threshold)
        finally:
            _analysis_semaphore.release()
    except Exception as e:
        logger.error(f"process_clip outer error session {session_id}: {e}", exc_info=True)
        update_session(session_id, status="failed", error_message=f"{type(e).__name__}: {e}")
    finally:
        if os.path.exists(clip_path):
            try:
                os.remove(clip_path)
            except Exception as ex:
                logger.warning(f"Cleanup failed {clip_path}: {ex}")


def _run_analysis(session_id: int, clip_path: str, context: dict,
                  examples: list = None, webhook_url: str = "",
                  confidence_threshold: float = 0.75):
    try:
        # Auto-detect game if requested
        if context.get("game") == "auto":
            import os as _os, time as _time
            from google import genai as _genai
            _api_key = _os.environ.get("GEMINI_API_KEY")
            if _api_key:
                from backend.agents.game_detector import detect_game_from_clip
                _client = _genai.Client(api_key=_api_key)
                detected = detect_game_from_clip(str(clip_path), _client)
                context = {**context, "game": detected}
                append_agent_log_event(session_id, {
                    "agent": "detector",
                    "action": "complete",
                    "detail": f"Auto-detected game: {detected}",
                    "iteration": 0,
                    "ts": _time.time(),
                })

        def log_callback(log: list):
            """Write the latest agent log to DB after each agent step."""
            if log:
                last = log[-1]
                append_agent_log_event(session_id, last)

        orchestrator = Orchestrator()
        result = orchestrator.run(
            str(clip_path), context, examples or [],
            log_callback=log_callback,
            confidence_threshold=confidence_threshold,
        )

        if not result:
            update_session(session_id, status="failed",
                           error_message="Orchestrator returned no result")
            return

        agent_log = result.pop("_agent_log", [])
        update_session(session_id,
                       full_result=json.dumps(result),
                       pegasus_analysis=json.dumps(agent_log))

        clip_duration = get_clip_duration(str(clip_path))
        for j, m in enumerate(result.get("mistakes", [])):
            clip_ts      = m.get("timestamp", 0)
            clip_filename = f"s{session_id}_m{j}.mp4"
            out_path     = CLIPS_DIR / clip_filename
            clip_web     = None
            try:
                start = max(0.0, clip_ts - 5)
                end   = min(clip_ts + 10, clip_duration) if clip_duration > 0 else clip_ts + 10
                if end > start:
                    extract_clip(str(clip_path), start, end, str(out_path))
                    clip_web = f"/clips/{clip_filename}"
            except Exception as e:
                logger.error(f"Clip extraction failed for mistake {j}: {e}")
            save_mistake(session_id, {**m, "clip_path": clip_web})

        update_session(session_id, status="complete")
        logger.info(f"Session {session_id} completed.")

        # Fire webhook if configured
        if webhook_url:
            _fire_webhook(webhook_url, session_id)

    except Exception as e:
        logger.error(f"Analysis session {session_id} failed: {e}", exc_info=True)
        update_session(session_id, status="failed", error_message=f"{type(e).__name__}: {e}")


def _fire_webhook(url: str, session_id: int):
    try:
        import httpx
        httpx.post(url, json={"session_id": session_id, "status": "complete"}, timeout=10)
        logger.info(f"Webhook fired → {url} for session {session_id}")
    except Exception as e:
        logger.warning(f"Webhook failed ({url}): {e}")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze(
    background_tasks: BackgroundTasks,
    clip: UploadFile = File(...),
    game: str = Form("r6siege"),
    attacking_team: str = Form("Attackers"),
    defending_team: str = Form("Defenders"),
    winner: str = Form("Unknown"),
    round_number: int = Form(1),
    notes: str = Form(""),
    webhook_url: str = Form(""),
    min_confidence: float = Form(0.75),
    custom_game_description: str = Form(""),
):
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    # Clamp confidence threshold
    min_confidence = max(0.0, min(1.0, min_confidence))

    session_id = create_session(
        clip.filename, game, attacking_team, defending_team, winner, round_number, notes,
        webhook_url=webhook_url, confidence_threshold=min_confidence
    )

    content = await clip.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413,
                            detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024**3)} GB.")

    clip_path = UPLOADS_DIR / f"{session_id}_{clip.filename}"
    with open(clip_path, "wb") as f:
        f.write(content)

    context = {
        "game":                    game,
        "attacking_team":          attacking_team,
        "defending_team":          defending_team,
        "winner":                  winner,
        "round_number":            round_number,
        "notes":                   notes,
        "custom_game_description": custom_game_description,
    }

    examples = get_top_examples(game=game, limit=2)
    background_tasks.add_task(
        process_clip, session_id, clip_path, context, examples,
        webhook_url, min_confidence
    )
    return {"session_id": session_id, "status": "uploading"}


@router.get("/status/{session_id}")
async def status(session_id: int):
    s = get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": s["status"], "error": s.get("error_message")}


@router.get("/log/{session_id}")
async def agent_log(session_id: int):
    """Real-time agent log for pipeline progress display."""
    s = get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    log = get_agent_log_live(session_id)
    return {"session_id": session_id, "status": s["status"], "log": log}


@router.get("/results/{session_id}")
async def results(session_id: int):
    data = get_results(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data


@router.get("/report/{session_id}.pdf")
async def download_pdf(session_id: int):
    """Generate and stream a PDF coaching report."""
    data = get_results(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    if data.get("status") != "complete":
        raise HTTPException(status_code=400, detail="Analysis not complete yet")

    session  = get_session(session_id)
    result   = data.get("full_result", {})
    mistakes = data.get("mistakes", [])

    # Re-attach sub-reports from full_result into result for PDF
    for key in ("next_round_plan", "trend_report"):
        if key in result:
            pass  # already present
    try:
        pdf_bytes = generate_pdf(session, result, mistakes)
    except Exception as e:
        logger.error(f"PDF generation failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"asc-session-{session_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/segment-vod")
async def segment_vod(
    background_tasks: BackgroundTasks,
    vod: UploadFile = File(...),
    game: str = Form("r6siege"),
    attacking_team: str = Form("Attackers"),
    defending_team: str = Form("Defenders"),
):
    """
    Upload a full VOD. Gemini identifies round boundaries, then each round
    is extracted and queued as a separate analysis session automatically.
    Returns a list of {session_id, round_number, start_s, end_s}.
    """
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    content = await vod.read()
    vod_path = UPLOADS_DIR / f"vod_{vod.filename}"
    with open(vod_path, "wb") as f:
        f.write(content)

    segments = _segment_vod_sync(str(vod_path), game, attacking_team, defending_team)
    if not segments:
        os.remove(vod_path)
        raise HTTPException(status_code=422, detail="Could not detect round boundaries in this VOD.")

    results_list = []
    for seg in segments:
        clip_filename = f"vod_r{seg['round_number']}_{vod.filename}"
        out_path      = UPLOADS_DIR / clip_filename
        try:
            extract_clip(str(vod_path), seg["start_s"], seg["end_s"], str(out_path))
        except Exception as e:
            logger.warning(f"Could not extract round {seg['round_number']}: {e}")
            continue

        sid = create_session(
            clip_filename, game, attacking_team, defending_team,
            "Unknown", seg["round_number"], f"Auto-segmented from {vod.filename}"
        )
        context = {
            "game":           game,
            "attacking_team": attacking_team,
            "defending_team": defending_team,
            "winner":         "Unknown",
            "round_number":   seg["round_number"],
            "notes":          f"Auto-segmented from {vod.filename}",
        }
        examples = get_top_examples(game=game, limit=2)
        background_tasks.add_task(process_clip, sid, out_path, context, examples)
        results_list.append({
            "session_id":   sid,
            "round_number": seg["round_number"],
            "start_s":      seg["start_s"],
            "end_s":        seg["end_s"],
        })

    try:
        os.remove(vod_path)
    except Exception:
        pass

    return {"segments": results_list, "total_rounds": len(results_list)}


def _segment_vod_sync(vod_path: str, game: str, atk: str, defn: str) -> list[dict]:
    """
    Use Gemini to identify round timestamps in a VOD.
    Returns [{round_number, start_s, end_s}, ...]
    """
    import os, time
    from google import genai as _genai
    from google.genai import types as _types
    from backend.agents.game_config import get_config
    from backend.utils.gemini_client import _extract_json

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return []

    client = _genai.Client(api_key=api_key)
    cfg    = get_config(game)

    try:
        uploaded = client.files.upload(file=vod_path, config={"mime_type": "video/mp4"})
        for _ in range(30):
            f = client.files.get(name=uploaded.name)
            if f.state.name == "ACTIVE":
                break
            if f.state.name == "FAILED":
                return []
            time.sleep(3)
        else:
            return []

        prompt = (
            f"This is a {cfg['name']} VOD. {atk} vs {defn}.\n"
            f"Identify where each round starts and ends.\n"
            f"A round is {cfg['min_round_seconds']}–{cfg['max_round_seconds']} seconds long.\n"
            f"There should be a gap of at least {cfg['min_gap_between_rounds']} seconds between rounds (buy phase/lobby).\n\n"
            f"Return ONLY valid JSON:\n"
            f'[{{"round_number": 1, "start_s": <int>, "end_s": <int>}}, ...]\n\n'
            f"Only include rounds you can clearly see. Do not guess."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded, prompt],
            config=_types.GenerateContentConfig(
                thinking_config=_types.ThinkingConfig(thinking_budget=4000)
            )
        )

        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass

        segments = _extract_json(response.text)
        if not isinstance(segments, list):
            return []

        # Validate each segment
        valid = []
        for seg in segments:
            if not all(k in seg for k in ("round_number", "start_s", "end_s")):
                continue
            duration = seg["end_s"] - seg["start_s"]
            if not (cfg["min_round_seconds"] <= duration <= cfg["max_round_seconds"]):
                continue
            valid.append(seg)

        return sorted(valid, key=lambda x: x["round_number"])

    except Exception as e:
        logger.error(f"VOD segmentation failed: {e}", exc_info=True)
        return []


@router.get("/sessions")
async def sessions(limit: int = 100):
    return {"sessions": list_sessions(limit=limit)}


@router.get("/search")
async def search(q: str, game: str = None, limit: int = 10):
    """Semantic similarity search over all stored mistakes using embeddings."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results = semantic_search_mistakes(q.strip(), game=game, limit=limit)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/patterns")
async def patterns(game: str = None, limit: int = 500, n_clusters: int = 5):
    """Cluster stored mistake embeddings to surface recurring tactical patterns."""
    mistakes = get_embedded_mistakes(game=game, limit=limit)
    if not mistakes:
        return {"clusters": [], "anomalies": [], "total_analyzed": 0,
                "message": "No embedded mistakes yet — run some analyses first"}
    from backend.ml.pattern_analyzer import analyze_mistake_patterns
    result = analyze_mistake_patterns(mistakes, n_clusters=n_clusters)
    result["game_filter"] = game
    return result


class FeedbackBody(BaseModel):
    rating: int
    notes: str = ""


@router.post("/feedback/{session_id}")
async def feedback(session_id: int, body: FeedbackBody):
    s = get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    if not 1 <= body.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1–5")
    save_feedback(session_id, body.rating, body.notes)
    return {"ok": True, "used_as_example": body.rating >= 4}
