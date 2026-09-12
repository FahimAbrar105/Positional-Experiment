"""Persists every trial to disk, in a shape that supports the thesis's later
item-level SD / mixed-effects analysis (sec 3.4), not just the graph.

Written under RESULTS_DIR:
  trials.csv          -- one row per trial (model, condition, resulting axis scores)
  item_responses.csv  -- one row per (trial, item), the raw response matrix R
  raw/<trial_id>.txt  -- the model's exact, verbatim reply for that trial
                         (including any repair follow-up) -- for auditing a
                         score back to exactly what the model said
"""
import csv
import json
import os
import uuid
from pathlib import Path

from .config import RESULTS_DIR
from .engine import TrialResult
from ..instruments.base import Instrument

_TRIALS_FILE = "trials.csv"
_ITEMS_FILE = "item_responses.csv"
_RAW_DIR = "raw"


def _ensure_dir():
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)


def _append_csv(filename: str, fieldnames: list[str], row: dict):
    _ensure_dir()
    path = os.path.join(RESULTS_DIR, filename)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


_TRIALS_FIELDNAMES = ["trial_id", "timestamp", "model_id", "instrument_name",
                      "condition_type", "condition_label", "elapsed_seconds",
                      "axes_summary", "axes_json"]


def save_trial(instrument: Instrument, trial: TrialResult) -> str:
    trial_id = str(uuid.uuid4())

    # Different instruments have different trait/axis names (2 for Political Compass,
    # up to 7 for MFV), so those can't be fixed CSV columns without the column set
    # drifting -- and silently misaligning -- every time you switch instruments in
    # the same session. axes_json keeps the schema stable; axes_summary is just for
    # eyeballing the file directly.
    axes_summary = "; ".join(f"{name}={value:.3f}" for name, value in trial.score.axes.items())
    trial_row = {
        "trial_id": trial_id,
        "timestamp": trial.timestamp,
        "model_id": trial.model_id,
        "instrument_name": trial.instrument_name,
        "condition_type": trial.condition_type,
        "condition_label": trial.condition_label,
        "elapsed_seconds": trial.elapsed_seconds,
        "axes_summary": axes_summary,
        "axes_json": json.dumps(trial.score.axes),
    }
    _append_csv(_TRIALS_FILE, _TRIALS_FIELDNAMES, trial_row)

    raw_dir = Path(RESULTS_DIR) / _RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{trial_id}.txt").write_text(trial.raw_model_text, encoding="utf-8")

    block_by_item = {it.item_id: it.block for it in instrument.items}
    item_fieldnames = ["trial_id", "model_id", "condition_type", "condition_label",
                        "item_id", "block", "position", "value"]
    for position, item_id in enumerate(trial.displayed_order, start=1):
        _append_csv(_ITEMS_FILE, item_fieldnames, {
            "trial_id": trial_id,
            "model_id": trial.model_id,
            "condition_type": trial.condition_type,
            "condition_label": trial.condition_label,
            "item_id": item_id,
            "block": block_by_item.get(item_id, ""),
            "position": position,
            "value": trial.responses.get(item_id),
        })

    return trial_id
