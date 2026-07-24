"""EvalBench AI - Database Models. 100% local SQLite via SQLAlchemy."""
from datetime import datetime
from sqlalchemy import (create_engine, Column, Integer, String, Float, Boolean,
                         DateTime, Text, ForeignKey)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./data/evalbench.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    version = Column(Integer, default=1)
    template = Column(Text)
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("EvalRun", back_populates="prompt")


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    examples = relationship("DatasetExample", back_populates="dataset")


class DatasetExample(Base):
    __tablename__ = "dataset_examples"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    input_text = Column(Text)
    reference_answer = Column(Text, nullable=True)
    context = Column(Text, nullable=True)  # for RAG eval

    dataset = relationship("Dataset", back_populates="examples")


class EvalRun(Base):
    __tablename__ = "eval_runs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    model_name = Column(String, default="phi3")
    status = Column(String, default="pending")  # pending, running, done, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    prompt = relationship("Prompt", back_populates="runs")
    results = relationship("EvalResult", back_populates="run")


class EvalResult(Base):
    __tablename__ = "eval_results"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("eval_runs.id"))
    example_id = Column(Integer)
    input_text = Column(Text)
    generated_output = Column(Text)
    reference_answer = Column(Text, nullable=True)
    context = Column(Text, nullable=True)

    judge_score = Column(Float, nullable=True)
    correctness = Column(Float, nullable=True)
    relevance = Column(Float, nullable=True)
    coherence = Column(Float, nullable=True)
    judge_reasoning = Column(Text, nullable=True)

    hallucination_score = Column(Float, nullable=True)
    hallucination_flag = Column(Boolean, default=False)
    unsupported_claims = Column(Text, nullable=True)

    context_precision = Column(Float, nullable=True)
    context_recall = Column(Float, nullable=True)
    faithfulness = Column(Float, nullable=True)
    answer_relevancy = Column(Float, nullable=True)

    latency_ms = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("EvalRun", back_populates="results")


class ABTest(Base):
    __tablename__ = "ab_tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    run_a_id = Column(Integer, ForeignKey("eval_runs.id"))
    run_b_id = Column(Integer, ForeignKey("eval_runs.id"))
    winner = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
