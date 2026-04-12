#!/bin/bash
set -e
# For WSL/Linux
apt-get update && apt-get install -y ffmpeg python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data/vods data/clips
echo "Setup complete. Run backend: uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo "Run frontend: streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"
