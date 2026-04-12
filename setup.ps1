$ErrorActionPreference = "Stop"

# Create virtual environment if it doesn't exist
if (-not (Test-Path -Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
. .venv\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
Write-Host "Creating data directories..."
New-Item -ItemType Directory -Force -Path "data\vods"
New-Item -ItemType Directory -Force -Path "data\clips"

Write-Host "Setup complete."
Write-Host "Run backend: uvicorn backend.main:app --host 0.0.0.0 --port 8000"
Write-Host "Run frontend: streamlit run frontend\app.py --server.port 8501 --server.address 0.0.0.0"
