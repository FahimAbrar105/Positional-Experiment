"""Item-ordering conditions used in the position-manipulation design.

Three condition types:
  - baseline:      original order, exactly as published.
  - full_shuffle:  every item independently randomized.
  - full_reversal: the entire item order reversed (last item first).
"""
import random
from dataclasses import dataclass


@dataclass
class Item:
    item_id: str      # stable id, e.g. the instrument's own field/key name
    text: str
    block: str
    reverse: bool = False  # True if this item is reverse-SCORED (unrelated to item order)


def full_shuffle(items: list[Item], rng: random.Random | None = None) -> list[Item]:
    rng = rng or random.Random()
    shuffled = list(items)
    rng.shuffle(shuffled)
    return shuffled


def full_reversal(items: list[Item]) -> list[Item]:
    return list(reversed(items))


def baseline_order(items: list[Item]) -> list[Item]:
    return list(items)
