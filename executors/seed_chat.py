from __future__ import annotations

from typing import Any
import json
import re

from .modelark import ModelArkClient


def decompose_procedure(
    client: ModelArkClient,
    model: str,
    transcript: str,
    step_count: int = 6,
    reference_context: str | None = None,
) -> dict[str, Any]:
    prompt = (
        "Convert the transcript into a strict JSON object with a top-level 'steps' array. "
        "Each step must include: step, title, action, hazards, prompt_for_keyframe, "
        "motion_prompt, narration. Make the language concrete for skilled-trades training. "
        "When reference context is provided, treat manufacturer and text-based sources as the "
        "authority for sequence and safety language, and treat YouTube references only as "
        "visual blocking guidance. "
        f"Target {step_count} steps.\n\n"
    )
    if reference_context:
        prompt += f"Reference context:\n{reference_context}\n\n"
    prompt += f"Transcript:\n{transcript}"
    response = client.post_json(
        "/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        },
    )
    content = _extract_content(response)
    return _extract_json_object(content)


def _extract_content(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError("Seed chat response did not include choices.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [item.get("text", "") for item in content if item.get("type") in {"text", "output_text"}]
        return "".join(text_parts)
    raise RuntimeError(f"Unsupported chat content payload: {message!r}")


def _extract_json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise RuntimeError("No JSON object found in Seed chat response.")
        return json.loads(match.group(0))
