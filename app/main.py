"""
EvalBench AI - FastAPI Backend
Prompt versioning, datasets, evaluation runs, A/B testing, and analytics. Fully local.
"""
import json
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import (init_db, get_db, Prompt, Dataset, DatasetExample,
                                  EvalRun, EvalResult, ABTest)
from app.core.orchestrator import EvalOrchestrator
from app.core.ab_testing import ABTester

app = FastAPI(title="EvalBench AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
init_db()


class PromptCreate(BaseModel):
    name: str
    template: str
    system_prompt: Optional[str] = None


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ExampleCreate(BaseModel):
    input_text: str
    reference_answer: Optional[str] = None
    context: Optional[str] = None


class RunCreate(BaseModel):
    name: str
    prompt_id: int
    dataset_id: int
    model_name: str = "phi3"
    rag_mode: bool = False


class ABTestCreate(BaseModel):
    name: str
    run_a_id: int
    run_b_id: int


@app.get("/")
def root():
    return {"platform": "EvalBench AI", "status": "online", "mode": "100% local"}


@app.post("/prompts")
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db)):
    latest = (db.query(Prompt).filter(Prompt.name == payload.name)
              .order_by(Prompt.version.desc()).first())
    version = (latest.version + 1) if latest else 1
    prompt = Prompt(name=payload.name, version=version, template=payload.template,
                     system_prompt=payload.system_prompt)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@app.get("/prompts")
def list_prompts(db: Session = Depends(get_db)):
    return db.query(Prompt).order_by(Prompt.name, Prompt.version.desc()).all()


@app.post("/datasets")
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    ds = Dataset(name=payload.name, description=payload.description)
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@app.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).all()


@app.post("/datasets/{dataset_id}/examples")
def add_example(dataset_id: int, payload: ExampleCreate, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    ex = DatasetExample(dataset_id=dataset_id, input_text=payload.input_text,
                         reference_answer=payload.reference_answer, context=payload.context)
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex


@app.post("/datasets/{dataset_id}/examples/bulk")
def add_examples_bulk(dataset_id: int, examples: List[ExampleCreate], db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    for payload in examples:
        db.add(DatasetExample(dataset_id=dataset_id, input_text=payload.input_text,
                               reference_answer=payload.reference_answer, context=payload.context))
    db.commit()
    return {"added": len(examples)}


@app.get("/datasets/{dataset_id}/examples")
def get_examples(dataset_id: int, db: Session = Depends(get_db)):
    return db.query(DatasetExample).filter(DatasetExample.dataset_id == dataset_id).all()


@app.post("/runs")
def create_and_execute_run(payload: RunCreate, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == payload.prompt_id).first()
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not prompt or not dataset:
        raise HTTPException(404, "Prompt or dataset not found")

    run = EvalRun(name=payload.name, prompt_id=payload.prompt_id, dataset_id=payload.dataset_id,
                  model_name=payload.model_name, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    examples = db.query(DatasetExample).filter(DatasetExample.dataset_id == payload.dataset_id).all()
    example_dicts = [{"id": e.id, "input_text": e.input_text,
                       "reference_answer": e.reference_answer, "context": e.context} for e in examples]

    orchestrator = EvalOrchestrator(model_name=payload.model_name, rag_mode=payload.rag_mode)
    results = orchestrator.run_dataset(prompt.template, prompt.system_prompt, example_dicts)

    for r in results:
        db.add(EvalResult(
            run_id=run.id, example_id=r.get("example_id"), input_text=r["input_text"],
            generated_output=r["generated_output"], reference_answer=r.get("reference_answer"),
            context=r.get("context"), judge_score=r.get("judge_score"),
            correctness=r.get("correctness"), relevance=r.get("relevance"),
            coherence=r.get("coherence"), judge_reasoning=r.get("judge_reasoning"),
            hallucination_score=r.get("hallucination_score"),
            hallucination_flag=r.get("hallucination_flag", False),
            unsupported_claims=r.get("unsupported_claims"),
            context_precision=r.get("context_precision"), context_recall=r.get("context_recall"),
            faithfulness=r.get("faithfulness"), answer_relevancy=r.get("answer_relevancy"),
            latency_ms=r.get("latency_ms"), error=r.get("error"),
        ))

    run.status = "done"
    run.completed_at = datetime.utcnow()
    db.commit()
    return {"run_id": run.id, "status": "done", "num_results": len(results)}


@app.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    return db.query(EvalRun).order_by(EvalRun.created_at.desc()).all()


@app.get("/runs/{run_id}/results")
def get_run_results(run_id: int, db: Session = Depends(get_db)):
    return db.query(EvalResult).filter(EvalResult.run_id == run_id).all()


@app.get("/runs/{run_id}/summary")
def get_run_summary(run_id: int, db: Session = Depends(get_db)):
    results = db.query(EvalResult).filter(EvalResult.run_id == run_id).all()
    if not results:
        return {"num_results": 0}
    scores = [r.judge_score for r in results if r.judge_score is not None]
    hallu = [r.hallucination_score for r in results if r.hallucination_score is not None]
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    flagged = sum(1 for r in results if r.hallucination_flag)
    return {
        "num_results": len(results),
        "avg_judge_score": round(sum(scores) / len(scores), 3) if scores else None,
        "avg_hallucination_score": round(sum(hallu) / len(hallu), 3) if hallu else None,
        "hallucination_flag_rate": round(flagged / len(results), 3),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else None,
    }


@app.post("/ab-tests")
def run_ab_test(payload: ABTestCreate, db: Session = Depends(get_db)):
    run_a = db.query(EvalRun).filter(EvalRun.id == payload.run_a_id).first()
    run_b = db.query(EvalRun).filter(EvalRun.id == payload.run_b_id).first()
    if not run_a or not run_b:
        raise HTTPException(404, "One or both runs not found")

    scores_a = [r.judge_score for r in db.query(EvalResult).filter(EvalResult.run_id == run_a.id)
                if r.judge_score is not None]
    scores_b = [r.judge_score for r in db.query(EvalResult).filter(EvalResult.run_id == run_b.id)
                if r.judge_score is not None]

    tester = ABTester()
    result = tester.compare(run_a.name, scores_a, run_b.name, scores_b)

    ab = ABTest(name=payload.name, run_a_id=run_a.id, run_b_id=run_b.id,
                winner=result.winner, summary=result.summary)
    db.add(ab)
    db.commit()
    db.refresh(ab)

    return {
        "id": ab.id, "winner": result.winner, "mean_score_a": result.mean_score_a,
        "mean_score_b": result.mean_score_b, "p_value_estimate": result.p_value_estimate,
        "summary": result.summary,
    }


@app.get("/ab-tests")
def list_ab_tests(db: Session = Depends(get_db)):
    return db.query(ABTest).order_by(ABTest.created_at.desc()).all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
