"""Procedural clouds for the blank sky above the picture: soft blotches, stronger on grey days."""

import random
from dataclasses import dataclass

from PIL import Image, ImageChops

from .config import SKY_CLOUD_GAIN

# Cloud strength per weather condition (1.0 = heavy overcast); unlisted conditions get UNKNOWN's.
_STRENGTHS = {
    "clear": 0.25,
    "partly_cloudy": 0.6,
    "fog": 0.4,
    "overcast": 1.0,
    "rain": 1.0,
    "thunderstorm": 1.0,
    "snow": 1.0,
}
_UNKNOWN_STRENGTH = 0.4
# Blotch sizes (px), from big cloud banks to small wisps, and how much each adds to the mix.
_OCTAVES = ((520, 1.0), (220, 0.45), (90, 0.2))
_NEUTRAL = 128


@dataclass(frozen=True)
class Clouds:
    strength: float
    seed: int


def clouds_for(condition: str, seed: int) -> Clouds:
    return Clouds(_STRENGTHS.get(condition, _UNKNOWN_STRENGTH), seed)


def add_clouds(sky: Image.Image, clouds: Clouds) -> Image.Image:
    """The grayscale `sky` with light and dark cloud blotches added around its own tone."""
    rng = random.Random(clouds.seed)
    mix = None
    for size, weight in _OCTAVES:
        layer = _blotches(sky.size, size, rng)
        mix = layer if mix is None else Image.blend(mix, layer, weight / (1 + weight))
    gain = clouds.strength * SKY_CLOUD_GAIN
    offsets = mix.point(lambda value: _NEUTRAL + round((value - _NEUTRAL) * gain))
    return ImageChops.add(sky, offsets, scale=1, offset=-_NEUTRAL)


def _blotches(size: tuple[int, int], feature: int, rng: random.Random) -> Image.Image:
    """Smooth random noise whose blotches are about `feature` px across."""
    columns, rows = max(2, size[0] // feature + 2), max(2, size[1] // feature + 2)
    grid = Image.frombytes(
        "L", (columns, rows), bytes(rng.randrange(256) for _ in range(columns * rows))
    )
    return grid.resize(size, Image.Resampling.BICUBIC)
