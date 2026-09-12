"""Thin client for querying a model on OpenRouter."""
import os
import time
import requests
from .config import OPENROUTER_API_URL

_RATE_LIMIT_RETRY_DELAYS = [5, 15, 30]  # seconds; free-tier upstream pools get busy
_MALFORMED_RETRY_DELAYS = [3, 8]        # some free providers occasionally return a body with no `choices`

_SITE_URL = "https://github.com/"
_APP_NAME = "thesis-position-bias-pilot"

# Some free models (observed: NVIDIA's Nemotron family) will happily burn their
# ENTIRE completion budget on internal reasoning and return empty content, even
# with a qualitative {"effort": "low"} hint -- one measured case spent 618
# reasoning tokens just to say "Hello". A hard token cap on reasoning, rather
# than a qualitative hint, is what actually guarantees budget survives for the
# real answer; verified against a full 62-item prompt before adopting this.
_REASONING_TOKEN_CAP = 4000


def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and fill in your key."
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": _SITE_URL,
        "X-Title": _APP_NAME,
    }


def _extract_content(model_id: str, data: dict, max_tokens: int) -> str:
    if "error" in data:
        raise RuntimeError(f"OpenRouter error for {model_id}: {data['error']}")
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
    """Sends a full chat-completion request (arbitrary message history) and
    returns the assistant's text content. Falls back to no `reasoning` param
    if a model rejects it outright."""
    base_payload = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    payload = {**base_payload, "reasoning": {"max_tokens": _REASONING_TOKEN_CAP}}
    resp = requests.post(OPENROUTER_API_URL, headers=_headers(), json=payload, timeout=timeout)
    if resp.status_code == 400 and "reasoning" in resp.text.lower():
        payload = base_payload
        resp = requests.post(OPENROUTER_API_URL, headers=_headers(), json=payload, timeout=timeout)

    for delay in _RATE_LIMIT_RETRY_DELAYS:
        if resp.status_code != 429:
            break
        time.sleep(delay)
        resp = requests.post(OPENROUTER_API_URL, headers=_headers(), json=payload, timeout=timeout)

    resp.raise_for_status()
    data = resp.json()

    # A handful of free-tier providers occasionally return 200 with a body that
    # never got a real completion (no `choices` at all) under load -- retrying
    # the same request a couple of times resolves it in practice.
    for delay in _MALFORMED_RETRY_DELAYS:
        if "error" in data or data.get("choices"):
            break
        time.sleep(delay)
        resp = requests.post(OPENROUTER_API_URL, headers=_headers(), json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

    return _extract_content(model_id, data, max_tokens)


def query_model(model_id: str, system_prompt: str, user_prompt: str, temperature: float = 0.0,
                 max_tokens: int = 16000, timeout: int = 240) -> str:
    """Convenience wrapper for a single system+user turn."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return query_chat(model_id, messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
