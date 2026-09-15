"""Small OpenAI-compatible adapter for hosted, non-deterministic reasoning."""

import json
import re
from typing import Any

import httpx

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT_SECONDS


def is_configured() -> bool:
    return bool(LLM_API_KEY and LLM_API_KEY.strip())


def _json_from_content(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: search for first `{` and last `}`
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def complete_json(system_prompt: str, user_payload: dict) -> dict:
    """Call a chat-completions compatible endpoint and parse strict JSON."""
    if not is_configured():
        raise RuntimeError("LLM_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "BugFix AI",
    }
    url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"

    payload: dict[str, Any] = {
        "model": LLM_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt + "\nReturn ONLY raw valid JSON."},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
        ],
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=LLM_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Some providers (OpenRouter free models) reject response_format with 400 or 422.
        # Retry without it so plain JSON extraction handles the response.
        if exc.response.status_code in (400, 422) and "response_format" in payload:
            payload.pop("response_format", None)
            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=LLM_TIMEOUT_SECONDS)
                response.raise_for_status()
            except httpx.HTTPStatusError as retry_exc:
                raise RuntimeError(
                    f"LLM provider returned {retry_exc.response.status_code}: {retry_exc.response.text[:400]}"
                ) from retry_exc
        else:
            raise RuntimeError(
                f"LLM provider returned {exc.response.status_code}: {exc.response.text[:400]}"
            ) from exc

    body: dict[str, Any] = response.json()
    content = body["choices"][0]["message"]["content"]
    return _json_from_content(content)


def generate_findings(context: dict, matches: list[dict]) -> dict:
    return complete_json(
        """You are a senior software defect diagnostician. Analyze the supplied bug context and retrieved historical evidence. Return only JSON with keys root_cause and remediation. root_cause must contain status, hypothesis, confidence_score (0 to 1), reasoning, supporting_evidence (array). remediation must contain status and recommendations (array of objects with recommendation, basis, supporting_bug_id, supporting_evidence, confidence_score). Never claim certainty unsupported by evidence. Clearly label historical evidence versus reasoning. If evidence is weak, use insufficient_evidence.""",
        {"bug_context": context, "historical_evidence": matches[:8]},
    )


def generate_followup(report: dict, history: list[dict], question: str) -> str:
    try:
        result = complete_json(
            """You are a careful bug-diagnosis assistant. Answer the user's follow-up using only the diagnosis report and conversation context. Distinguish retrieved evidence from inference, state uncertainty, and give concrete engineering guidance. Return JSON with one key answer containing concise Markdown text.""",
            {"diagnosis_report": report, "conversation": history[-12:], "question": question},
        )
    except Exception as exc:
        raise RuntimeError(f"Follow-up generation failed: {exc}") from exc
    answer = result.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        # LLM returned unexpected shape — extract any string value as the answer
        for value in result.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
        raise ValueError("Hosted model returned no answer")
    return answer.strip()