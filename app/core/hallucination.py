"""EvalBench AI - Hallucination Detection. Fully local via Ollama + lexical fallback."""
import re
import ollama
from dataclasses import dataclass
from typing import List, Optional
from app.core.json_utils import extract_json

HALLUCINATION_SYSTEM_PROMPT = """You are a fact-consistency checker. Respond ONLY with JSON:
{"hallucination_score": <0.0-1.0>, "unsupported_claims": ["<claim>"], "reasoning": "<explanation>"}"""

@dataclass
class HallucinationResult:
    score: float
    flagged: bool
    unsupported_claims: List[str]
    reasoning: str

class HallucinationDetector:
    def __init__(self, model: str = "phi3", flag_threshold: float = 0.4):
        self.model = model
        self.flag_threshold = flag_threshold

    def _lexical_overlap_score(self, context: str, output: str) -> float:
        if not context: return 0.5
        ctx = set(re.findall(r"\w+", context.lower()))
        out = re.findall(r"\w+", output.lower())
        if not out: return 0.0
        return min(1.0, len([w for w in out if w not in ctx and len(w) > 4]) / max(1, len(out)))

    def detect(self, generated_output: str, context: Optional[str] = None) -> HallucinationResult:
        try:
            response = ollama.chat(model=self.model, stream=False,
                messages=[{"role": "system", "content": HALLUCINATION_SYSTEM_PROMPT},
                           {"role": "user", "content": f"Context: {context or 'N/A'}\n\nGenerated output: {generated_output}"}],
                options={"temperature": 0.0, "num_predict": 512})
            data = extract_json(response["message"]["content"])
            if data is None: raise ValueError("parse failed")
            score = max(0.0, min(1.0, float(data.get("hallucination_score", 0.5))))
            claims = data.get("unsupported_claims", [])
            if not isinstance(claims, list): claims = [str(claims)]
            reasoning = str(data.get("reasoning", ""))
        except Exception:
            score = self._lexical_overlap_score(context or "", generated_output)
            claims, reasoning = [], "Fallback lexical-overlap heuristic used."
        return HallucinationResult(round(score,3), score >= self.flag_threshold, claims, reasoning)
