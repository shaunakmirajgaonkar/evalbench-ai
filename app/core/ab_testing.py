"""
EvalBench AI - A/B Testing
Statistically compares two eval runs (e.g. two prompt versions or two models)
using local aggregate metrics and an LLM-based summary. No cloud calls.
"""
import ollama
import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class ABTestResult:
    winner: str  # 'A', 'B', 'tie'
    mean_score_a: float
    mean_score_b: float
    p_value_estimate: float
    summary: str


class ABTester:
    def __init__(self, model: str = "phi3"):
        self.model = model

    @staticmethod
    def _bootstrap_p_value(scores_a: List[float], scores_b: List[float], n_boot: int = 2000) -> float:
        """Simple local bootstrap test for difference in means, no scipy dependency required."""
        if not scores_a or not scores_b:
            return 1.0
        a, b = np.array(scores_a), np.array(scores_b)
        observed_diff = a.mean() - b.mean()
        pooled = np.concatenate([a, b])
        n_a = len(a)
        count = 0
        rng = np.random.default_rng(42)
        for _ in range(n_boot):
            rng.shuffle(pooled)
            diff = pooled[:n_a].mean() - pooled[n_a:].mean()
            if abs(diff) >= abs(observed_diff):
                count += 1
        return round(count / n_boot, 4)

    def compare(self, run_a_name: str, scores_a: List[float],
                run_b_name: str, scores_b: List[float]) -> ABTestResult:
        mean_a = round(float(np.mean(scores_a)), 3) if scores_a else 0.0
        mean_b = round(float(np.mean(scores_b)), 3) if scores_b else 0.0
        p_value = self._bootstrap_p_value(scores_a, scores_b)

        if p_value > 0.05:
            winner = "tie"
        else:
            winner = "A" if mean_a > mean_b else "B"

        summary = self._generate_summary(run_a_name, mean_a, run_b_name, mean_b, winner, p_value)
        return ABTestResult(winner=winner, mean_score_a=mean_a, mean_score_b=mean_b,
                             p_value_estimate=p_value, summary=summary)

    def _generate_summary(self, name_a, mean_a, name_b, mean_b, winner, p_value) -> str:
        prompt = (f"Run A ('{name_a}') mean quality score: {mean_a}/10. "
                  f"Run B ('{name_b}') mean quality score: {mean_b}/10. "
                  f"Statistical result: winner={winner}, p-value estimate={p_value}. "
                  "Write a concise 2-3 sentence plain-English summary of this A/B test result "
                  "for an ML engineer, noting whether the difference is likely meaningful.")
        try:
            response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}],
                                    stream=False, options={"temperature": 0.3})
            return response["message"]["content"].strip()
        except Exception:
            return (f"{name_a} scored {mean_a}/10 vs {name_b} at {mean_b}/10 "
                    f"(bootstrap p≈{p_value}). Winner: {winner}.")
