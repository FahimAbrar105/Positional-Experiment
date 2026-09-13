"""Thin client for querying a model on Groq's free tier.

Groq's API is OpenAI-compatible but NOT identical to OpenRouter's: it uses
`max_completion_tokens` (not `max_tokens`) and a flat `reasoning_effort`
string (not OpenRouter's nested `{"reasoning": {"effort": ...}}`). Valid
reasoning_effort values differ per model, per Groq's documentation:
  openai/gpt-oss-120b / -20b : low | medium | high   (cannot disable)
  qwen/qwen3.6-27b           : none | default
  qwen/qwen3.8-27b           : none | default | low | medium | high
"""
import os
import time
import requests

_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_RATE_LIMIT_RETRY_DELAYS = [5, 15, 30]
_MALFORMED_RETRY_DELAYS = [3, 8]  # mirrors openrouter_client.py's defensiveness, for parity


def _api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at console.groq.com and add it to .env."
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _extract_content(model_id: str, data: dict, max_tokens: int) -> str:
    if "error" in data:
        raise RuntimeError(f"Groq error for {model_id}: {data['error']}")
    choices = data.get("choices")
    if not choices:
        raise RuntimeError(f"{model_id} returned a response with no choices: {data}")
    message = choices[0]["message"]
    content = message.get("content") or ""
    if not content and message.get("reasoning"):
        raise RuntimeError(
            f"{model_id} returned only reasoning tokens, no final content. "
            f"Try raising max_tokens (currently {max_tokens})."
        )
    return content


def query_chat(model_id: str, messages: list[dict], temperature: float = 0.0,
                max_tokens: int = 16000, reasoning_effort: str | None = None,
                timeout: int = 240) -> str:
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "reasoning_format": "hidden",  # only the final answer in `content`, no <think> noise to parse around
    }
    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort

    resp = requests.post(_API_URL, headers=_headers(), json=payload, timeout=timeout)

    for delay in _RATE_LIMIT_RETRY_DELAYS:
        if resp.status_code != 429:
            break
        time.sleep(delay)
        resp = requests.post(_API_URL, headers=_headers(), json=payload, timeout=timeout)

    resp.raise_for_status()
    data = resp.json()

    for delay in _MALFORMED_RETRY_DELAYS:
        if "error" in data or data.get("choices"):
            break
        time.sleep(delay)
        resp = requests.post(_API_URL, headers=_headers(), json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

    return _extract_content(model_id, data, max_tokens)


def query_model(model_id: str, system_prompt: str, user_prompt: str, temperature: float = 0.0,
                 max_tokens: int = 16000, reasoning_effort: str | None = None) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return query_chat(model_id, messages, temperature=temperature, max_tokens=max_tokens,
                       reasoning_effort=reasoning_effort)
