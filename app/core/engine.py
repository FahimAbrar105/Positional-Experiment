"""Runs one trial: build a prompt in some item order, query a model, score the result."""
import random
import time
from dataclasses import dataclass, field

from .latin_square import Item, baseline_order, full_shuffle, full_reversal
from . import llm_client
from ..instruments.base import Instrument, ScoreResult

MAX_REPAIR_ATTEMPTS = 2


@dataclass
class TrialResult:
    model_id: str
    instrument_name: str
    condition_type: str        # "baseline" | "full_shuffle" | "full_reversal"
    condition_label: str       # e.g. "shuffle #5" or "full_reversal"
    displayed_order: list[str]  # item_ids in the order shown to the model
    responses: dict[str, int]   # item_id -> numeric value
    score: ScoreResult
    raw_model_text: str
    elapsed_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)


def build_display_order(instrument: Instrument, condition_type: str,
                         rng: random.Random | None = None) -> list[Item]:
    if condition_type == "baseline":
        return baseline_order(instrument.items)
    if condition_type == "full_shuffle":
        return full_shuffle(instrument.items, rng=rng)
    if condition_type == "full_reversal":
        return full_reversal(instrument.items)
    raise ValueError(f"Unknown condition_type: {condition_type}")


def run_trial(instrument: Instrument, model_entry: dict, condition_type: str, condition_label: str,
              rng: random.Random | None = None, temperature: float = 0.0) -> TrialResult:
    """model_entry is one of config.MODELS -- {"id", "label", "provider", ...} --
    so llm_client knows which backend (OpenRouter vs Groq) to route the call to."""
    displayed = build_display_order(instrument, condition_type, rng=rng)

    system_prompt = instrument.build_system_prompt()
    user_prompt = instrument.build_user_prompt(displayed)

    start = time.time()
    last_reply = llm_client.query_model(model_entry, system_prompt, user_prompt, temperature=temperature)
    raw_text = last_reply

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    for _ in range(MAX_REPAIR_ATTEMPTS):
        missing = instrument.missing_positions(raw_text, displayed)
        if not missing:
            break
        messages.append({"role": "assistant", "content": last_reply})
        messages.append({"role": "user", "content": (
            f"You missed item(s) {missing}. Reply with ONLY those, same format "
            f"('<number>: <CODE>', one per line), nothing else."
        )})
        try:
            last_reply = llm_client.query_chat(model_entry, messages, temperature=temperature)
        except Exception:
            # A failed repair call (e.g. the model burns its whole budget on internal
            # reasoning and returns nothing) shouldn't crash the trial with an opaque
            # API error -- better to just stop retrying and let parse_response below
            # raise its normal, readable "still missing item(s) N" message.
            break
        raw_text = instrument.merge_repair(raw_text, last_reply)

    elapsed = time.time() - start

    responses = instrument.parse_response(raw_text, displayed)
    score = instrument.score(responses)

    return TrialResult(
        model_id=model_entry["id"],
        instrument_name=instrument.name,
        condition_type=condition_type,
        condition_label=condition_label,
        displayed_order=[it.item_id for it in displayed],
        responses=responses,
        score=score,
        raw_model_text=raw_text,
        elapsed_seconds=elapsed,
    )
