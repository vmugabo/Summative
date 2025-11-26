#!/usr/bin/env bash
set -euo pipefail

# Create a venv if missing, install requirements, and run the FastAPI app.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
VENV_DIR="$REPO_ROOT/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

cd "$REPO_ROOT"
echo "Starting uvicorn (API.prediction:app) on 0.0.0.0:8000"
exec uvicorn API.prediction:app --host 0.0.0.0 --port 8000 --reload
