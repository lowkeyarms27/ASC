# ASC: Agentic Strategic Coach

## Overview

ASC is a multi-agent AI system that watches esports gameplay clips and produces structured coaching reports. Upload a round clip, and a pipeline of 9 parallel ML sources feeding into 7 specialist AI agents will return timestamped tactical mistakes, video clip evidence, actionable alternatives, trend analysis across sessions, and a next-round strategy plan — in minutes.

Built for competitive esports teams to eliminate manual VOD review time. Supports Rainbow Six Siege, Valorant, CS2, Apex Legends, League of Legends, Dota 2, Overwatch 2, Mobile Legends, Marvel Rivals, and custom games.

---

## How It Works

Analysis runs in two phases.

**Phase 1 — Observation (parallel)**

Nine sources run simultaneously to build a complete picture of what happened in the clip:

| Source | What it captures |
|---|---|
| Gemini 2.5 Flash | Full video — factual timestamped event log |
| Twelve Labs Pegasus | Video semantic understanding and search |
| NVIDIA Cosmos Reason | Spatial reasoning — player positioning |
| YOLOv8 (PyTorch) | Frame-by-frame object and player detection |
| ByteTrack | Player movement tracking across frames |
| EasyOCR | HUD text — kill feed, scores, timers |
| OpenAI Whisper | Audio transcript — comms and callouts |
| Librosa | Audio event detection — shots and spikes |
| OpenAI CLIP | Visual concept and action recognition per frame |

A Gemini context cache is created after upload so video tokens are only charged once across all downstream agents.

**Phase 2 — Agent pipeline (sequential)**

The fused event log is passed through seven specialist agents:

1. **Observer** — Fuses all 9 sources into a unified timestamped event log
2. **Tactician** — Interprets the log tactically; uses function calling to re-examine specific timestamps before flagging a mistake
3. **Debater** — Adversarially challenges every finding to force the system to defend or drop weak claims
4. **Critic** — Scores confidence on surviving findings; filters anything below the configured threshold
5. **Coach** — Writes the final actionable report with specific better alternatives
6. **Statistician + Planner** — Cross-references past sessions for trend patterns; builds a next-round strategy plan
7. **Scenario** — Runs counterfactual prediction: what would have happened if the mistake was corrected

---

## Key Features

**Adversarial debate loop**
Every finding is challenged by the Debater before it reaches the user. Prevents hallucinated or weak mistakes from making it into the final report.

**Confidence thresholding**
Configurable from 50–100%. Lower gives more findings, higher keeps only unambiguous mistakes. The Critic scores each finding and removes anything below the threshold.

**Examine timestamp tool**
The Tactician uses Gemini function calling to re-examine specific seconds in the clip before committing to a finding — a verification step that catches misidentified events.

**Semantic search**
Every mistake is embedded with sentence-transformers and stored in SQLite. Search across all past sessions with natural language queries.

**Pattern clustering**
sklearn k-means clusters mistake embeddings across sessions to surface recurring tactical weaknesses automatically.

**PDF export**
Downloadable coaching report with full analysis, phase breakdown, and mistake list.

**Multi-game support**
Auto-detect mode uses Gemini to identify the game from the clip. All game-specific coaching prompts, phase labels, and round configs live in `backend/agents/game_config.py`.

---

## What It Outputs

- **KPI dashboard** — Total, critical, major, minor mistake counts; validated finding count
- **Phase breakdown** — Setup / Mid-Round / Endgame narrative for the round
- **Timestamped mistakes** — Each with severity, category, description, confidence score, Debater verdict, better alternative, and an extracted 15-second video clip
- **Strengths** — Observable things the winning team did well
- **Next Round Plan** — Setup adjustments, utility plan, coordinated plays, positions to avoid
- **Trend Report** — Cross-session win rates, improving and regressing categories, coaching priority
- **PDF export** — Full downloadable coaching report

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Primary AI | Gemini 2.5 Flash (Google) |
| Video AI | Twelve Labs Pegasus |
| Spatial AI | NVIDIA Cosmos Reason |
| Object detection | YOLOv8 (Ultralytics) |
| Player tracking | ByteTrack |
| Speech | OpenAI Whisper |
| Vision-language | OpenAI CLIP |
| OCR | EasyOCR |
| Audio | Librosa |
| Database | SQLite |
| Video processing | FFmpeg |
| Embeddings | sentence-transformers |
| Deployment | Vultr (Ubuntu 24.04), systemd, uvicorn |

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- FFmpeg installed and on PATH
- API keys: Google Gemini (billing enabled), Twelve Labs (optional), NVIDIA (optional)

---

## Quick Start

**1. Clone the repository**
```bash
git clone https://github.com/lowkeyarms27/ASC.git
cd ASC
```

**2. Set up the Python backend**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment**
```bash
cp .env.example .env
```
Add your API keys to `.env`:
```
GEMINI_API_KEY=your_key_here
TWELVELABS_API_KEY=your_key_here   # optional
ASC_API_KEY=your_secret_here       # protects the API
```

**4. Start the backend**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**5. Build and serve the frontend**
```bash
cd frontend-react
npm install
npm run build
```

The built frontend is served automatically by FastAPI at `http://localhost:8000`.

**Development mode** (hot reload):
```bash
cd frontend-react
echo "VITE_API_KEY=your_secret_here" > .env.local
npm run dev   # runs at http://localhost:5173, proxies /api to :8000
```

---

## Project Structure

```
ASC/
├── backend/
│   ├── agents/
│   │   ├── observer.py          # Phase 1: fuses 9 sources into event log
│   │   ├── tactician.py         # Tactical analysis with timestamp tool calling
│   │   ├── debater.py           # Adversarial challenge loop
│   │   ├── critic.py            # Confidence scoring and filtering
│   │   ├── coach.py             # Final coaching report writer
│   │   ├── statistician.py      # Cross-session trend analysis
│   │   ├── planner.py           # Next-round strategy generation
│   │   ├── scenario.py          # Counterfactual prediction
│   │   ├── orchestrator.py      # Pipeline coordinator
│   │   ├── game_config.py       # Per-game prompts and configuration
│   │   └── tools.py             # examine_timestamp function tool
│   ├── ml/
│   │   ├── yolo_analyzer.py     # YOLOv8 frame detection
│   │   ├── whisper_transcriber.py
│   │   ├── clip_analyzer.py     # CLIP visual concepts
│   │   ├── ocr_analyzer.py      # EasyOCR HUD reading
│   │   ├── player_tracker.py    # ByteTrack movement tracking
│   │   ├── audio_analyzer.py    # Librosa event detection
│   │   ├── embedder.py          # sentence-transformers embeddings
│   │   └── pattern_analyzer.py  # k-means mistake clustering
│   ├── routes/
│   │   └── analysis.py          # API endpoints
│   ├── utils/
│   │   ├── gemini_client.py
│   │   ├── twelvelabs_client.py
│   │   ├── video_processor.py   # FFmpeg clip extraction
│   │   └── pdf_generator.py
│   ├── database.py              # SQLite sessions and mistakes
│   ├── main.py                  # FastAPI app, serves React build
│   └── config.py
├── frontend-react/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AnalyzeClip.jsx  # Upload form + live pipeline + results
│   │   │   └── History.jsx      # Session browser + semantic search
│   │   ├── components/
│   │   │   ├── Analysis.jsx     # Full analysis render component
│   │   │   ├── Pipeline.jsx     # Live pipeline progress display
│   │   │   └── Topbar.jsx
│   │   └── lib/
│   │       ├── api.js           # Typed API client
│   │       └── constants.js
│   ├── vite.config.js
│   └── package.json
├── requirements.txt
└── setup.sh
```

---

## Architecture Notes

**Why adversarial debate?**
LLMs hallucinate. A single-pass analysis will flag events that didn't happen. The Debater agent is given the tactical findings and instructed to find reasons each mistake is wrong or overstated. The Critic then scores whether the Tactician's rebuttal holds up. Only findings that survive this loop make it to the user.

**Why 9 parallel sources?**
Gemini is strong at high-level understanding but can miss specific details (exact kill timings, HUD state, audio cues). The local ML sources provide ground-truth signals — OCR reads the kill feed, YOLO counts players on screen, Whisper captures callouts. The Tactician uses all of them together to make claims it can actually defend.

**Context caching**
The video is uploaded to Gemini once. A context cache is created so the Observer's generate_content call doesn't re-charge video input tokens for each subsequent agent. The Tactician uses the uploaded file directly (rather than the cache) so it retains access to the `examine_timestamp` function tool, which the Gemini API does not allow alongside cached content.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google AI API key with billing enabled |
| `TWELVELABS_API_KEY` | No | Twelve Labs key for Pegasus analysis |
| `NVIDIA_API_KEY` | No | NVIDIA key for Cosmos spatial reasoning |
| `ASC_API_KEY` | No | Shared secret added to all API requests |
| `BACKEND_URL` | No | Backend origin (default: same host) |

---

## Cost

Gemini 2.5 Flash charges per minute of video. Approximate costs per analysis:

- Short clip (1–2 min): ~$0.003–0.006
- Full round clip (3–5 min): ~$0.01–0.015
- Full 14-round match: ~$0.13

Context caching reduces repeated video token charges by approximately 6× across the agent pipeline.
