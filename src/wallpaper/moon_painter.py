"""Paint the moon, in its phase, onto the wallpaper (image models draw moon phases unreliably)."""

import math
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .config import (
    MOON_CENTER_X_RATIOS,
    MOON_CENTER_Y_RATIO,
    MOON_LEVEL,
    MOON_RADIUS_RATIO,
    SKY_SIDES,
)
from .moon_phase import PHASES

_SUPERSAMPLE = 4
_HALO_BLUR_RATIO = 0.6  # of the moon radius
_HALO_STRENGTH = 0.35
_WAXING_PHASES = PHASES[1 : PHASES.index("full") + 1]


@dataclass(frozen=True)
class Moon:
    phase: str
    side: str


def paint_moon(canvas: Image.Image, moon: Moon) -> None:
    """Paint onto a grayscale canvas in place. A new moon has no lit part, so nothing is painted."""
    if moon.phase not in PHASES:
        raise ValueError(f"unknown moon phase: {moon.phase!r}")
    if moon.side not in SKY_SIDES:
        raise ValueError(f"unknown moon side: {moon.side!r}")

    radius = round(canvas.width * MOON_RADIUS_RATIO)
    margin = 2 * radius  # room for the soft halo around the disc
    lit = _lit_part(radius, moon.phase)
    layer = Image.new("L", (lit.width + 2 * margin, lit.height + 2 * margin), 0)
    layer.paste(lit, (margin, margin))
    halo = layer.filter(ImageFilter.GaussianBlur(radius * _HALO_BLUR_RATIO))
    halo = halo.point(lambda value: round(value * _HALO_STRENGTH))

    center_x = round(canvas.width * MOON_CENTER_X_RATIOS[moon.side])
    center_y = round(canvas.height * MOON_CENTER_Y_RATIO)
    top_left = (center_x - layer.width // 2, center_y - layer.height // 2)
    canvas.paste(MOON_LEVEL, top_left, ImageChops.lighter(layer, halo))


def _lit_part(radius: int, phase: str) -> Image.Image:
    """Mask of the sunlit part of the disc: right side for a waxing moon, left for a waning one."""
    scale = radius * _SUPERSAMPLE
    size = 2 * scale + 1
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    angle = PHASES.index(phase) * 2 * math.pi / len(PHASES)  # 0 = new, pi = full
    terminator = math.cos(angle)
    for row in range(size):
        half_chord = math.sqrt(max(0.0, 1 - ((row - scale) / scale) ** 2))
        if phase in _WAXING_PHASES:
            start, end = terminator * half_chord, half_chord
        else:
            start, end = -half_chord, -terminator * half_chord
        if end > start:
            draw.line([(scale + start * scale, row), (scale + end * scale, row)], fill=255)
    return mask.resize((2 * radius + 1, 2 * radius + 1), Image.Resampling.LANCZOS)
