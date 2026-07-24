"""
EvalBench AI - Evaluation Orchestrator
Runs a full evaluation pipeline over a dataset: generate -> judge -> hallucination
check -> (optional) RAG metrics. Fully local end to end.
"""
from typing import List, Dict, Callable, Optional
from app.core.model_runner import ModelRunner
from app.core.llm_judge import LLMJudge
from app.core.hallucination import HallucinationDetector
from app.core.rag_metrics import RAGEvaluator


class EvalOrchestrator:
    def __init__(self, model_name: str = "phi3", rag_mode: bool = False):
        self.runner = ModelRunner(model_name)
        self.judge = LLMJudge(model_name)
        self.hallucination_detector = HallucinationDetector(model_name)
        self.rag_evaluator = RAGEvaluator(model_name) if rag_mode else None
        self.rag_mode = rag_mode

    def run_example(self, prompt_template: str, system_prompt: Optional[str],
                     input_text: str, reference_answer: Optional[str] = None,
                     context: Optional[str] = None) -> Dict:
        gen = self.runner.generate(prompt_template, input_text, system_prompt, context)

        result = {
            "input_text": input_text,
            "generated_output": gen.output,
            "reference_answer": reference_answer,
            "context": context,
            "latency_ms": gen.latency_ms,
        }

        if gen.error:
            result["error"] = gen.error
            return result

        judge_result = self.judge.evaluate(input_text, gen.output, reference_answer)
        result.update({
            "judge_score": judge_result.overall_score,
            "correctness": judge_result.correctness,
            "relevance": judge_result.relevance,
            "coherence": judge_result.coherence,
            "judge_reasoning": judge_result.reasoning,
        })

        hallu = self.hallucination_detector.detect(gen.output, context or reference_answer)
        result.update({
            "hallucination_score": hallu.score,
            "hallucination_flag": hallu.flagged,
            "unsupported_claims": "; ".join(hallu.unsupported_claims) if hallu.unsupported_claims else "",
        })

        if self.rag_mode and context:
            rag = self.rag_evaluator.evaluate(input_text, gen.output, context, reference_answer)
            result.update({
                "context_precision": rag.context_precision,
                "context_recall": rag.context_recall,
                "faithfulness": rag.faithfulness,
                "answer_relevancy": rag.answer_relevancy,
            })

        return result

    def run_dataset(self, prompt_template: str, system_prompt: Optional[str],
                     examples: List[Dict], on_progress: Callable[[int, int], None] = None) -> List[Dict]:
        results = []
        total = len(examples)
        for i, ex in enumerate(examples):
            r = self.run_example(
                prompt_template, system_prompt,
                ex["input_text"], ex.get("reference_answer"), ex.get("context")
            )
            r["example_id"] = ex.get("id")
            results.append(r)
            if on_progress:
                on_progress(i + 1, total)
        return results
