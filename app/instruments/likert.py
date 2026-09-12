"""Generic numeric-Likert self-report instrument: N items, each rated on an
integer scale, grouped into blocks (subscales/foundations/traits) that are
scored as the mean of their items (reverse-recoded where flagged).

Used directly by BFI-44 and SD3, and subclassed lightly by MFQ-30 (mixed
relevance/agreement wording) and MFV (wrongness rating, no reverse items).
"""
import re

from ..core.latin_square import Item
from .base import Instrument, ScoreResult


class LikertInstrument(Instrument):
    def __init__(self, name: str, items: list[Item], blocks: list[str],
                 scale_min: int, scale_max: int, scale_anchors: dict[int, str],
                 instructions: str, item_prefix: str = ""):
        self.name = name
        self.items = items
        self.blocks = blocks
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.scale_anchors = scale_anchors
        self.instructions = instructions
        self.item_prefix = item_prefix
        self.scale = [(str(v), v) for v in range(scale_min, scale_max + 1)]

    def build_system_prompt(self) -> str:
        anchor_lines = "\n".join(f"{v} = {label}" for v, label in sorted(self.scale_anchors.items()))
        return (
            f"{self.instructions}\n\n"
            f"Scale:\n{anchor_lines}\n\n"
            "Respond with exactly one line per item, in the form:\n"
            "<number>: <integer>\n"
            "Output nothing else -- no explanations, no repeated item text, "
            "just the numbered lines, one per item, in order."
        )

    def build_user_prompt(self, displayed_items: list[Item]) -> str:
        return "\n".join(f"{i}. {self.item_prefix}{it.text}" for i, it in enumerate(displayed_items, start=1))

    def _extract_positions(self, raw_text: str) -> dict[int, int]:
        # (?:^|\s) rather than a line-anchored ^ -- some free-tier models
        # (observed with a large, ~130-item instrument) occasionally run every
        # answer together on one line ("1: 6 2: 3 3: 5 ...") instead of one
        # per line despite instructions. The scale_min/max range check below
        # keeps this safe: a stray "N: V" found inside ordinary item text
        # would need to coincidentally land in-range to be accepted.
        found: dict[int, int] = {}
        pattern = re.compile(r"(?:^|\s)(\d+)\s*[.:)]\s*(-?\d+)")
        for m in pattern.finditer(raw_text):
            n = int(m.group(1))
            v = int(m.group(2))
            if self.scale_min <= v <= self.scale_max:
                found[n] = v
        return found

    def missing_positions(self, raw_text: str, displayed_items: list[Item]) -> list[int]:
        found = self._extract_positions(raw_text)
        return [i for i in range(1, len(displayed_items) + 1) if i not in found]

    def parse_response(self, raw_text: str, displayed_items: list[Item]) -> dict[str, int]:
        found = self._extract_positions(raw_text)
        missing = self.missing_positions(raw_text, displayed_items)
        if missing:
            raise ValueError(
                f"Could not parse a valid answer for item position(s) {missing} "
                f"out of {len(displayed_items)}. Raw model output:\n{raw_text}"
            )
        responses: dict[str, int] = {}
        for i, it in enumerate(displayed_items, start=1):
            responses[it.item_id] = found[i]
        return responses

    def _recode(self, item: Item, value: int) -> int:
        return (self.scale_min + self.scale_max) - value if item.reverse else value

    def score(self, responses: dict[str, int]) -> ScoreResult:
        by_block: dict[str, list[int]] = {b: [] for b in self.blocks}
        for it in self.items:
            by_block[it.block].append(self._recode(it, responses[it.item_id]))

        axes = {b: (sum(vals) / len(vals) if vals else 0.0) for b, vals in by_block.items()}
        axis_ranges = {b: (float(self.scale_min), float(self.scale_max)) for b in self.blocks}
        return ScoreResult(axes=axes, axis_ranges=axis_ranges)
