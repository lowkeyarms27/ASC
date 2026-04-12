from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from backend.routes.analysis import router
from backend.database import init_db
import os
import time
import logging
from contextlib import asynccontextmanager
from backend.config import CLIPS_DIR, UPLOADS_DIR

DIST_DIR = Path(__file__).parent.parent / "frontend-dist"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def _cleanup_old_clips(max_age_days: int = 30):
    """Delete mistake clips older than max_age_days to prevent disk accumulation."""
    cutoff = time.time() - (max_age_days * 86400)
    removed = 0
    for f in CLIPS_DIR.glob("s*_m*.mp4"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        except Exception:
            pass
    if removed:
        logger.info(f"Cleaned up {removed} clip(s) older than {max_age_days} days")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    logger.info(f"Storage directories ready: {CLIPS_DIR.resolve()}")
    init_db()
    _cleanup_old_clips()
    yield



app = FastAPI(title="ASC Backend", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Enforce x-api-key on /api/ routes if ASC_API_KEY is set in the environment."""
    required_key = os.environ.get("ASC_API_KEY")
    if required_key and request.url.path.startswith("/api/"):
        # PDF reports are direct browser navigations — no custom headers possible
        if request.url.path.startswith("/api/report/"):
            return await call_next(request)
        if request.headers.get("x-api-key") != required_key:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)


app.include_router(router, prefix="/api")
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")

# Serve React frontend
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(DIST_DIR / "favicon.svg")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(DIST_DIR / "index.html")
