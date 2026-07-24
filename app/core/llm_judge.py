"""EvalBench AI - LLM-as-Judge. Fully local via Ollama."""
import ollama
from dataclasses import dataclass
from typing import Optional
from app.core.json_utils import extract_json

JUDGE_SYSTEM_PROMPT = """You are an impartial evaluator for LLM outputs. Score the output
on three axes from 0-10. Respond ONLY with this JSON, no markdown, no prose:
{"correctness": <0-10>, "relevance": <0-10>, "coherence": <0-10>, "overall_score": <0-10>, "reasoning": "<1-3 sentences>"}"""

@dataclass
class JudgeResult:
    correctness: float
    relevance: float
    coherence: float
    overall_score: float
    reasoning: str

class LLMJudge:
    def __init__(self, model: str = "phi3"):
        self.model = model

    def evaluate(self, input_text: str, generated_output: str,
                 reference_answer: Optional[str] = None) -> JudgeResult:
        user_content = (f"User input: {input_text}\n\nModel output: {generated_output}\n\n"
                        f"Reference answer: {reference_answer or 'N/A'}\n\nReturn the JSON scoring object only.")
        try:
            response = ollama.chat(model=self.model, stream=False,
                messages=[{"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                           {"role": "user", "content": user_content}],
                options={"temperature": 0.0, "num_predict": 512})
            raw = response["message"]["content"]
            data = extract_json(raw)
            if data is None:
                return JudgeResult(0, 0, 0, 0, f"Judge error: could not parse JSON: {raw[:200]!r}")
            def clamp(v):
                try: return max(0.0, min(10.0, float(v)))
                except: return 0.0
            return JudgeResult(clamp(data.get("correctness",0)), clamp(data.get("relevance",0)),
                               clamp(data.get("coherence",0)), clamp(data.get("overall_score",0)),
                               str(data.get("reasoning","")))
        except Exception as e:
            return JudgeResult(0, 0, 0, 0, f"Judge error: {e}")
