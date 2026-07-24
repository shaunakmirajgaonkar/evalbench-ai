# EvalBench AI

100% local LLM evaluation & benchmarking platform: LLM-as-judge, hallucination
detection, RAG metrics, prompt versioning, A/B testing, and analytics — all
running against local Ollama models with zero cloud calls.

## One-time setup

```bash
cd evalbench-ai
chmod +x setup.sh
./setup.sh
```

This creates a Python 3.12 virtual environment, installs all dependencies,
and creates the `data/` folder for the SQLite database.

If you don't have Ollama yet:
```bash
brew install ollama          # macOS
ollama pull phi3
```
(If Ollama is already running in the background, you do NOT need to run `ollama serve` — it's likely already listening on port 11434.)

## Run (every time)

**Terminal 1 — backend:**
```bash
cd evalbench-ai
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 2 — dashboard:**
```bash
cd evalbench-ai
source venv/bin/activate
python -m streamlit run dashboard/app.py
```

Dashboard: http://localhost:8501
API docs: http://localhost:8001/docs

Always use `python -m uvicorn` / `python -m streamlit` (not bare `uvicorn`/`streamlit`)
so the venv's Python is guaranteed to be used, even if your Mac has other
global Python installs.

## Workflow

1. **Create a prompt** (sidebar) — supports `{input}` and `{context}` placeholders, versioned automatically per name.
2. **Create a dataset** and add examples (manually or bulk CSV: `input_text, reference_answer, context`).
3. **Run Evaluation tab** — pick prompt + dataset + model, optionally enable RAG metrics, run.
4. **Run Results tab** — see judge scores, hallucination flags, per-example breakdown, and any generation/judging errors.
5. **A/B Testing tab** — compare two runs (e.g. prompt v1 vs v2) with a bootstrap significance test and LLM-generated summary.
6. **Analytics tab** — cross-run charts for score, hallucination rate, and latency trends.

## Notes on local model output parsing

Local models (phi3, llama3, etc.) don't always return perfectly clean JSON —
they may wrap it in markdown fences or add a sentence before/after it.
`app/core/json_utils.py` handles this robustly by trying direct parsing,
then brace-matching, then regex extraction, before falling back to safe
defaults. This is why judge/hallucination scores should no longer come
back as flat zeros due to parsing failures.

## Troubleshooting

- **`ModuleNotFoundError`**: your venv isn't active. Run `source venv/bin/activate` in that terminal, confirm with `which python` (should point inside `evalbench-ai/venv/bin/`).
- **`sqlite3.OperationalError: unable to open database file`**: the `data/` folder is missing — `mkdir -p data` and retry.
- **Connection refused on :8001**: the backend isn't running — start it per the "Run" section above.
- **All scores are 0.0**: this was a JSON-parsing bug in earlier versions, fixed in `app/core/json_utils.py`. Make sure you're on this version.
- **pyarrow segfault in Streamlit**: `requirements.txt` pins `pyarrow==14.0.2`, which is stable with pandas 2.2.2 on macOS ARM. Don't upgrade it independently.
