from dataclasses import dataclass, field
from ..core.latin_square import Item


@dataclass
class ScoreResult:
    axes: dict[str, float]          # e.g. {"Economic Left/Right": 0.38, "Social Lib/Auth": 2.41}
    axis_ranges: dict[str, tuple[float, float]]  # for plotting bounds, e.g. {"Economic...": (-10, 10)}
    extra: dict = field(default_factory=dict)    # any instrument-specific extras worth logging


class Instrument:
    """Common interface every instrument module implements."""

    name: str = ""
    items: list[Item] = []
    blocks: list[str] = []          # ordered list of block names, as designed by the researcher
    scale: list[tuple[str, int]] = []  # (code shown to the model, numeric value), e.g. [("SD",0),("D",1),("A",2),("SA",3)]

    def build_system_prompt(self) -> str:
        raise NotImplementedError

    def build_user_prompt(self, displayed_items: list[Item]) -> str:
        raise NotImplementedError

    def parse_response(self, raw_text: str, displayed_items: list[Item]) -> dict[str, int]:
        raise NotImplementedError

    def missing_positions(self, raw_text: str, displayed_items: list[Item]) -> list[int]:
        """Returns 1-indexed display positions with no parseable answer yet. Used for repair retries."""
        raise NotImplementedError

    def merge_repair(self, raw_text: str, repair_text: str) -> str:
        """Combines an original (incomplete) reply with a follow-up reply covering the gaps."""
        return raw_text.rstrip() + "\n" + repair_text.strip()

    def score(self, responses: dict[str, int]) -> ScoreResult:
        raise NotImplementedError
