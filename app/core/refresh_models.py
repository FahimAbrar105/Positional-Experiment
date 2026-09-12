"""Checks which models in config.MODELS are still free/available, across both
providers. Catalogs rotate over time (models get retired or added, or moved
behind paywalls -- this happened to Llama on Groq, for instance), so it's
worth re-running this every so often rather than trusting config.py blindly.

Usage:
    D:\\Thesis\\.venv\\Scripts\\python.exe -m app.core.refresh_models
"""
import os
import requests
from dotenv import load_dotenv

from .config import MODELS, OPENROUTER_MODELS_URL

load_dotenv()

_NON_CHAT_HINTS = ("lyria", "content-safety", "openrouter/free")
_GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
_GOOGLE_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/openai/models"
_OPENAI_MODELS_URL = "https://api.openai.com/v1/models"


def _is_usable_free_openrouter_model(m: dict) -> bool:
    pricing = m.get("pricing", {})
    if pricing.get("prompt") != "0" or pricing.get("completion") != "0":
        return False
    if "text" not in (m.get("architecture", {}).get("output_modalities") or ["text"]):
        return False
    if any(hint in m["id"] for hint in _NON_CHAT_HINTS):
        return False
    return True


def _check_openrouter():
    configured = [e for e in MODELS if e["provider"] == "openrouter"]
    resp = requests.get(OPENROUTER_MODELS_URL, timeout=30)
    resp.raise_for_status()
    all_models = {m["id"]: m for m in resp.json()["data"]}

    print("OpenRouter models in config.py:\n")
    for entry in configured:
        mid = entry["id"]
        m = all_models.get(mid)
        if m is None:
            print(f"  MISSING          {mid} -- no longer listed on OpenRouter at all")
        elif not _is_usable_free_openrouter_model(m):
            print(f"  NO LONGER FREE   {mid}")
        else:
            print(f"  OK               {mid}")

    configured_ids = {e["id"] for e in configured}
    others = [m for mid, m in all_models.items()
              if mid not in configured_ids and _is_usable_free_openrouter_model(m)]
    if others:
        print(f"\n{len(others)} other free OpenRouter text model(s) not in your list:\n")
        for m in sorted(others, key=lambda m: m["id"]):
            print(f"  {m['id']}  ({m.get('name', '')})")


def _check_groq():
    configured = [e for e in MODELS if e["provider"] == "groq"]
    key = os.environ.get("GROQ_API_KEY")
    print("\nGroq models in config.py:\n")
    if not key:
        print("  (skipped -- GROQ_API_KEY not set in .env, can't check without it)")
        for entry in configured:
            print(f"  ?  {entry['id']}  (unverified)")
        return

    resp = requests.get(_GROQ_MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    live_ids = {m["id"] for m in resp.json()["data"]}
    for entry in configured:
        status = "OK              " if entry["id"] in live_ids else "MISSING         "
        print(f"  {status} {entry['id']}")
    print("\n  Note: this only confirms the model still exists on Groq, not that it's\n"
          "  still on the free plan -- check console.groq.com/docs/rate-limits for that.")


def _check_google():
    configured = [e for e in MODELS if e["provider"] == "google"]
    if not configured:
        return
    key = os.environ.get("GEMINI_API_KEY")
    print("\nGoogle direct (Gemma) models in config.py:\n")
    if not key:
        print("  (skipped -- GEMINI_API_KEY not set in .env, can't check without it)")
        for entry in configured:
            print(f"  ?  {entry['id']}  (unverified)")
        return

    resp = requests.get(_GOOGLE_MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    # Google's listing prefixes ids with "models/" (e.g. "models/gemma-4-31b-it"),
    # but the chat completions endpoint wants the bare id -- strip it to compare.
    live_ids = {m["id"].removeprefix("models/") for m in resp.json()["data"]}
    for entry in configured:
        status = "OK              " if entry["id"] in live_ids else "MISSING         "
        print(f"  {status} {entry['id']}")


def _check_openai():
    configured = [e for e in MODELS if e["provider"] == "openai"]
    if not configured:
        return
    key = os.environ.get("OPENAI_API_KEY")
    print("\nOpenAI direct models in config.py (paid -- no free tier):\n")
    if not key:
        print("  (skipped -- OPENAI_API_KEY not set in .env, can't check without it)")
        for entry in configured:
            print(f"  ?  {entry['id']}  (unverified)")
        return

    resp = requests.get(_OPENAI_MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    resp.raise_for_status()
    live_ids = {m["id"] for m in resp.json()["data"]}
    for entry in configured:
        status = "OK              " if entry["id"] in live_ids else "MISSING         "
        print(f"  {status} {entry['id']}")
    print("\n  Note: this only confirms the model id still exists, not its current\n"
          "  price -- check platform.openai.com/docs/pricing for that.")


def main():
    _check_openrouter()
    _check_groq()
    _check_google()
    _check_openai()


if __name__ == "__main__":
    main()
