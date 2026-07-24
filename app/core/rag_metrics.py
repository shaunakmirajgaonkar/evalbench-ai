"""EvalBench AI - RAG Evaluation Metrics. Local embeddings + LLM judging."""
import numpy as np
import ollama
from dataclasses import dataclass
from typing import Optional
from app.core.json_utils import extract_json

_cache = {}

def _get_embedder():
    if "e" not in _cache:
        from sentence_transformers import SentenceTransformer
        _cache["e"] = SentenceTransformer("all-MiniLM-L6-v2")
    return _cache["e"]

def _cosine(a, b):
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / d) if d else 0.0

@dataclass
class RAGMetrics:
    context_precision: float
    context_recall: float
    faithfulness: float
    answer_relevancy: float

class RAGEvaluator:
    def __init__(self, model: str = "phi3", use_embeddings: bool = True):
        self.model = model
        self.use_embeddings = use_embeddings

    def _sim(self, a: str, b: str) -> float:
        try:
            e = _get_embedder().encode([a, b])
            return round(_cosine(e[0], e[1]), 3)
        except: return self._lex(a, b)

    @staticmethod
    def _lex(a: str, b: str) -> float:
        sa, sb = set(a.lower().split()), set(b.lower().split())
        return round(len(sa & sb) / len(sa | sb), 3) if sa and sb else 0.0

    def _faithfulness(self, context: str, answer: str) -> float:
        try:
            r = ollama.chat(model=self.model, stream=False,
                messages=[{"role":"system","content":'Respond ONLY with JSON: {"faithfulness": <0.0-1.0>}'},
                           {"role":"user","content":f"Context: {context}\n\nAnswer: {answer}"}],
                options={"temperature":0.0,"num_predict":128})
            d = extract_json(r["message"]["content"])
            return max(0.0, min(1.0, float(d.get("faithfulness", 0.5)))) if d else self._lex(context, answer)
        except: return self._lex(context, answer)

    def evaluate(self, question, answer, context, reference_context=None) -> RAGMetrics:
        s = self._sim if self.use_embeddings else self._lex
        return RAGMetrics(
            context_precision=s(question, context),
            context_recall=s(context, reference_context) if reference_context else s(question, context),
            faithfulness=self._faithfulness(context, answer),
            answer_relevancy=s(question, answer),
        )
