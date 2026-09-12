"""Provider-agnostic entry point: routes each model to whichever backend it's
configured for (config.MODELS carries a "provider" per model), so the rest of
the app (engine.py) never needs to know or care which API a model lives on.
"""
from . import openrouter_client, groq_client, google_client, openai_client


def query_model(model_entry: dict, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return query_chat(model_entry, messages, temperature=temperature)


def query_chat(model_entry: dict, messages: list[dict], temperature: float = 0.0) -> str:
    provider = model_entry.get("provider", "openrouter")
    model_id = model_entry["id"]

    if provider == "groq":
        return groq_client.query_chat(model_id, messages, temperature=temperature,
                                       reasoning_effort=model_entry.get("reasoning_effort"))
    if provider == "openrouter":
        return openrouter_client.query_chat(model_id, messages, temperature=temperature)
    if provider == "google":
        return google_client.query_chat(model_id, messages, temperature=temperature)
    if provider == "openai":
        return openai_client.query_chat(model_id, messages, temperature=temperature)
    raise ValueError(f"Unknown provider '{provider}' for model {model_id}")
