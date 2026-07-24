#!/usr/bin/env bash
# EvalBench AI - one-shot setup script (macOS/Linux)
# Usage: bash setup.sh
set -e

echo "== EvalBench AI setup =="

mkdir -p data

if [ ! -d "venv" ]; then
    echo "Creating virtual environment with python3.12..."
    PYBIN=$(command -v python3.12 || command -v python3)
    "$PYBIN" -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete."
echo "Next steps:"
echo "  1) In this terminal:      python -m uvicorn app.main:app --reload --port 8001"
echo "  2) In a NEW terminal tab: source venv/bin/activate && python -m streamlit run dashboard/app.py"
echo "  3) Make sure Ollama is running and phi3 is pulled: ollama pull phi3"
