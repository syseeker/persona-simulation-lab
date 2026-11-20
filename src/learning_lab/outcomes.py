"""Separate a model's public answer from transport and harness success."""

from __future__ import annotations

import json
import re


def answer_text(content) -> str:
    """Accept the text blocks used by maintained harnesses; never stringify objects."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        blocks = []
        for block in content:
            if isinstance(block, str):
                blocks.append(block)
            elif isinstance(block, dict) and block.get("type") in {"text", "output_text"}:
                if isinstance(block.get("text"), str):
                    blocks.append(block["text"])
        return "\n".join(blocks)
    return ""


def answer_outcome(content) -> dict:
    text = answer_text(content).strip()
    if not text:
        return {"status": "invalid", "code": "empty_answer", "reason": "No public answer was returned."}
    if re.fullmatch(r"(?:\[ERROR\s*:[\s\S]*?\]\s*)+", text, re.IGNORECASE):
        return {
            "status": "invalid",
            "code": "model_error_text",
            "reason": "The model returned error text as its answer. This is not proof of a local runtime exception.",
        }
    pseudo_tool = bool(re.search(r"<(?:tool_call|function[= >]|parameter[= >])", text, re.IGNORECASE))
    try:
        payload = json.loads(text)
        pseudo_tool = (
            pseudo_tool
            or isinstance(payload, dict)
            and bool(
                payload.get("tool_calls")
                or payload.get("tool_call")
                or payload.get("function")
                or (payload.get("name") and "arguments" in payload)
            )
        )
    except ValueError:
        pass
    if pseudo_tool:
        return {
            "status": "invalid",
            "code": "unparsed_tool_call",
            "reason": "The model returned tool-call markup as text instead of a structured tool call.",
        }
    return {
        "status": "valid",
        "code": "public_answer",
        "reason": "A nonempty public answer was saved; factual checks are separate.",
    }


class InvalidAnswer(RuntimeError):
    def __init__(self, outcome: dict):
        self.outcome = outcome
        super().__init__(outcome["reason"] + " Inspect the saved reply and native trace.")


def require_valid_answer(content) -> str:
    outcome = answer_outcome(content)
    if outcome["status"] != "valid":
        raise InvalidAnswer(outcome)
    return answer_text(content)
