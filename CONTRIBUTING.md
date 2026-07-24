# Contributing to EvalBench AI

Thanks for your interest in contributing!

## Getting started

1. Fork the repository and clone your fork
2. Run `./setup.sh` to create a virtual environment and install dependencies
3. Create a new branch: `git checkout -b feature/my-change`

## Development workflow

- Backend: `python -m uvicorn app.main:app --reload --port 8001`
- Dashboard: `python -m streamlit run dashboard/app.py`
- Make sure Ollama is running locally with a model pulled (e.g. `ollama pull phi3`)

## Submitting changes

1. Follow existing code style
2. Test your changes locally
3. Write a clear commit message
4. Open a pull request against `main`

## Code of Conduct

This project follows a Code of Conduct. By participating, you agree to uphold it.
