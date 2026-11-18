"""Choose the scenic spot for a given date and slot, without keeping any state."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .config import SLOTS

_REQUIRED_FIELDS = ("id", "name_ko", "area", "visual")


class SpotDataError(ValueError):
    """The spot list is unusable (malformed file, duplicate ids, too few spots)."""


@dataclass(frozen=True)
class Spot:
    id: str
    name_ko: str
    area: str
    visual: str


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
        spots.append(Spot(**{field: item[field] for field in _REQUIRED_FIELDS}))
    return spots


def cycle_length(spots: list[Spot]) -> int:
    """Days it takes to show every spot once (each day consumes one spot per slot)."""
    length = len(spots) // len(SLOTS)
    if length < 1:
        raise SpotDataError(f"at least {len(SLOTS)} spots are required, got {len(spots)}")
    return length


def select_spot(spots: list[Spot], on_date: date, slot: str) -> Spot:
    """Spots are reshuffled every cycle (seeded by the cycle number), then dealt out in order."""
    if slot not in SLOTS:
        raise ValueError(f"unknown slot: {slot!r}")
    cycle, offset = divmod(on_date.toordinal(), cycle_length(spots))
    order = sorted(spots, key=lambda spot: _rank(cycle, spot))
    return order[offset * len(SLOTS) + SLOTS.index(slot)]


def _rank(cycle: int, spot: Spot) -> str:
    return hashlib.sha256(f"{cycle}:{spot.id}".encode()).hexdigest()
