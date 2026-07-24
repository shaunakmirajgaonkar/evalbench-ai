"""
EvalBench AI - JSON Extraction Helper
Handles noisy/truncated LLM output (phi3 adds junk tokens, truncates JSON mid-stream).
No cloud calls - pure string/regex processing.
"""
import json
import re
from typing import Optional, Dict, Any


def _clean(raw: str) -> str:
    text = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE)
    text = re.sub(r"end_of_output\s*\|?\]?", "", text)
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"\[\|.*?\|\]", "", text)
    text = re.sub(r"\|\s*\]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _try_close_and_parse(text: str) -> Optional[Dict[str, Any]]:
    t = re.sub(r',\s*"?[^"]*"?\s*:?\s*[^,{}\[\]]*$', '', text.rstrip())
    t = t.rstrip().rstrip(',')
    open_b = t.count("{") - t.count("}")
    open_sq = t.count("[") - t.count("]")
    if open_b <= 0 and open_sq <= 0:
        return None
    t += "]" * max(0, open_sq)
    t += "}" * max(0, open_b)
    try:
        data = json.loads(t)
        return data if isinstance(data, dict) and data else None
    except (json.JSONDecodeError, ValueError):
        return None


def extract_json(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None
    text = _clean(raw_text)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    start = text.find("{")
    if start != -1:
        depth = 0
        end = -1
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end != -1:
            try:
                return json.loads(text[start:end + 1])
            except (json.JSONDecodeError, ValueError):
                pass
        recovered = _try_close_and_parse(text[start:])
        if recovered is not None:
            return recovered
    spans = list(set(re.findall(r"\{[^{}]*\}", text) + re.findall(r"\{.*\}", text, re.DOTALL)))
    for m in sorted(spans, key=len, reverse=True):
        try:
            return json.loads(m)
        except (json.JSONDecodeError, ValueError):
            continue
    return None
