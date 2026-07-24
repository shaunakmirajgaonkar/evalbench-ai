# Run Instructions

## One-time setup

cd evalbench-ai
chmod +x setup.sh
./setup.sh

If you don't have Ollama yet:
brew install ollama
ollama pull phi3

## Run (every time)

Terminal 1 — backend:
cd evalbench-ai
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8001

Terminal 2 — dashboard:
cd evalbench-ai
source venv/bin/activate
python -m streamlit run dashboard/app.py

Dashboard: http://localhost:8501
API docs: http://localhost:8001/docs
