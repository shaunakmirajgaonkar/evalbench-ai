"""
EvalBench AI - Model Runner
Executes prompts against local Ollama models and times generation. No cloud LLM calls.
"""
import time
import ollama
from dataclasses import dataclass


@dataclass
class GenerationResult:
    output: str
    latency_ms: float
    error: str = ""


class ModelRunner:
    def __init__(self, model: str = "phi3"):
        self.model = model

    def generate(self, prompt_template: str, input_text: str,
                 system_prompt: str = None, context: str = None) -> GenerationResult:
        rendered = prompt_template.replace("{input}", input_text).replace("{context}", context or "")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": rendered})

        start = time.time()
        try:
            response = ollama.chat(model=self.model, messages=messages, stream=False,
                                    options={"temperature": 0.3})
            latency_ms = (time.time() - start) * 1000
            return GenerationResult(output=response["message"]["content"].strip(), latency_ms=latency_ms)
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return GenerationResult(output="", latency_ms=latency_ms, error=str(e))
