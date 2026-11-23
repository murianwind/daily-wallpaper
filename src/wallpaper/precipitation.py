"""Paint rain streaks or snowflakes over the wallpaper, so a rainy or snowy day looks like one."""

import random
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .config import RAIN_LEVEL, RAIN_STREAKS, SNOW_FLAKES, SNOW_LEVEL

RAIN = "rain"
SNOW = "snow"

_RAIN_CONDITIONS = ("rain", "thunderstorm")
_SNOW_CONDITIONS = ("snow",)
_STREAK_LENGTH = (70, 150)  # px
_STREAK_WIDTH = 2
_STREAK_LEAN = 0.15  # horizontal px per vertical px, so the rain falls at a slant
_FLAKE_RADIUS = (2, 5)  # px
_SOFTEN_RADIUS = 0.8  # blur (px) that takes the hard pixel edge off the drawing


@dataclass(frozen=True)
class Precipitation:
    kind: str
    seed: int


def precipitation_for(condition: str, seed: int) -> Precipitation | None:
    """What to paint for a weather condition (None when it is dry)."""
    if condition in _RAIN_CONDITIONS:
        return Precipitation(RAIN, seed)
    if condition in _SNOW_CONDITIONS:
        return Precipitation(SNOW, seed)
    return None


def paint_precipitation(canvas: Image.Image, precipitation: Precipitation) -> None:
    """Add the streaks or flakes to a grayscale canvas in place."""
    rng = random.Random(precipitation.seed)
    layer = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(layer)
    if precipitation.kind == RAIN:
        _draw_streaks(draw, canvas.size, rng)
        level = RAIN_LEVEL
    elif precipitation.kind == SNOW:
        _draw_flakes(draw, canvas.size, rng)
        level = SNOW_LEVEL
    else:
        raise ValueError(f"unknown precipitation kind: {precipitation.kind!r}")

    layer = layer.filter(ImageFilter.GaussianBlur(_SOFTEN_RADIUS)).point(
        lambda value: round(value * level / 255)
    )
    canvas.paste(ImageChops.add(canvas, layer))


def _draw_streaks(draw: ImageDraw.ImageDraw, size: tuple[int, int], rng: random.Random) -> None:
    width, height = size
    for _ in range(RAIN_STREAKS):
        length = rng.randint(*_STREAK_LENGTH)
        x, y = rng.uniform(0, width + length * _STREAK_LEAN), rng.uniform(0, height)
        draw.line(
            [(x, y), (x - length * _STREAK_LEAN, y + length)],
            fill=rng.randint(150, 255),
            width=_STREAK_WIDTH,
        )


def _draw_flakes(draw: ImageDraw.ImageDraw, size: tuple[int, int], rng: random.Random) -> None:
    width, height = size
    for _ in range(SNOW_FLAKES):
        radius = rng.randint(*_FLAKE_RADIUS)
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=rng.randint(180, 255))
