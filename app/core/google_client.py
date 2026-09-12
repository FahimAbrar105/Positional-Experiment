"""Thin client for querying Gemma directly from Google's own free API --
bypassing OpenRouter's shared free pool entirely. Rate limits here are per
Google Cloud PROJECT (i.e. yours alone), not shared across every OpenRouter
free-tier user, which is the whole reason to use this path.

Uses Google's official OpenAI-compatibility layer, so the request/response
shape matches openrouter_client.py and groq_client.py -- only the base URL,
auth, and model id strings differ. Docs: ai.google.dev/gemini-api/docs/openai
"""
import os
import time
import requests

_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
_RATE_LIMIT_RETRY_DELAYS = [5, 15, 30]
_MALFORMED_RETRY_DELAYS = [3, 8]


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Get a free key at aistudio.google.com/apikey and add it to .env."
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _extract_content(model_id: str, data: dict, max_tokens: int) -> str:
    if "error" in data:
        raise RuntimeError(f"Google AI error for {model_id}: {data['error']}")
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
                max_tokens: int = 16000, timeout: int = 240) -> str:
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
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
                 max_tokens: int = 16000) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return query_chat(model_id, messages, temperature=temperature, max_tokens=max_tokens)
