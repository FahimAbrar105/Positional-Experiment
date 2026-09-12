"""Thin client for querying OpenAI's own API directly.

Verified against this account: gpt-4.1-nano and gpt-4o-mini both return
`credit_balance_exhausted` (no paid credits on this account), but gpt-5.6-luna
works anyway -- it appears to sit on some free/promotional allowance rather
than the account's paid balance, though OpenAI exposes no way to confirm that
distinction via API key (billing endpoints require browser session auth).

Important methodological caveat: gpt-5.6-luna rejects temperature=0 outright
("only the default (1) value is supported") -- unlike every other model in
this app, it cannot be made deterministic. query_chat() falls back to the
model's own default temperature when this happens rather than failing the
trial, but that means repeated "baseline" runs on this model may legitimately
disagree with each other for reasons unrelated to item order.
"""
import os
import time
import requests

_API_URL = "https://api.openai.com/v1/chat/completions"
_RATE_LIMIT_RETRY_DELAYS = [5, 15, 30]
_MALFORMED_RETRY_DELAYS = [3, 8]


def _api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add your existing OpenAI key to .env -- "
            "note OpenAI has no free tier, this will draw down your account's balance/credits."
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _extract_content(model_id: str, data: dict, max_tokens: int) -> str:
    if "error" in data:
        raise RuntimeError(f"OpenAI error for {model_id}: {data['error']}")
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
        "max_completion_tokens": max_tokens,
        # gpt-5.x models are reasoning-native; keep effort low to save tokens.
        # "minimal" is NOT a valid value for every gpt-5.x model (confirmed:
        # gpt-5.6-luna rejects it, wants none/low/medium/high/xhigh) -- "low"
        # is accepted everywhere tested. Falls back cleanly below regardless.
        "reasoning_effort": "low",
    }
    resp = requests.post(_API_URL, headers=_headers(), json=payload, timeout=timeout)

    if resp.status_code == 400 and "reasoning" in resp.text.lower():
        payload.pop("reasoning_effort", None)
        resp = requests.post(_API_URL, headers=_headers(), json=payload, timeout=timeout)

    if resp.status_code == 400 and "temperature" in resp.text.lower():
        # e.g. gpt-5.6-luna: "temperature does not support 0, only default (1)".
        # No client-side fix for this -- drop it and let the model use its own
        # default rather than fail the trial; caller/config should know this
        # model can't be made deterministic.
        payload.pop("temperature", None)
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
