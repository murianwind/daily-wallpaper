"""Load the scenic spots and pick one at random, avoiding the ones used recently."""

import json
import random
from dataclasses import dataclass
from pathlib import Path

_REQUIRED_FIELDS = ("id", "name_ko", "area", "visual")
_MIN_SPOTS = 2  # one spot to avoid (the latest) and at least one to choose


class SpotDataError(ValueError):
    """The spot list is unusable (malformed file, duplicate ids, too few spots)."""


@dataclass(frozen=True)
class Spot:
    id: str
    name_ko: str
    area: str
    visual: str
    waterfall: bool = False  # the falling water is the main subject (kept off the image centre)


def load_spots(path: Path) -> list[Spot]:
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    spots: list[Spot] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        missing = [field for field in _REQUIRED_FIELDS if not item.get(field)]
        if missing:
            raise SpotDataError(f"spot #{index} is missing: {', '.join(missing)}")
        if item["id"] in seen_ids:
            raise SpotDataError(f"duplicate spot id: {item['id']}")
        seen_ids.add(item["id"])
        waterfall = item.get("waterfall", False)
        if not isinstance(waterfall, bool):
            raise SpotDataError(f"spot #{index}: waterfall must be true or false")
        spots.append(
            Spot(**{field: item[field] for field in _REQUIRED_FIELDS}, waterfall=waterfall)
        )
    return spots


def history_window(spots: list[Spot]) -> int:
    """How many recent spots are avoided: half the list, so the other half stays eligible."""
    if len(spots) < _MIN_SPOTS:
        raise SpotDataError(f"at least {_MIN_SPOTS} spots are required, got {len(spots)}")
    return len(spots) // 2


def choose_spot(spots: list[Spot], recent_ids: list[str], rng: random.Random) -> Spot:
    """A random spot that is not among the `history_window` most recently used ones."""
    avoided = set(recent_ids[: history_window(spots)])
    return rng.choice([spot for spot in spots if spot.id not in avoided])
