"""Turn the raw generated image into an iPhone-sized grayscale JPEG.

The picture is trimmed, fitted into the lower part of the screen, darkened if it is too bright (so
iOS shows white text on it) and the top third is left as a plain blank background that the picture
fades into. The moon, if any, is painted last so the darkening does not dim it.
"""

import io

from PIL import Image, ImageStat, UnidentifiedImageError

from .config import EDGE_TRIM_RATIO, MAX_MEAN_BRIGHTNESS, TOP_BLANK_RATIO, TOP_FADE_RATIO
from .moon_painter import Moon, paint_moon

JPEG_QUALITY = 92
_OPAQUE = 255
# Caps the darkening so a near-white picture is not crushed to solid black.
_MAX_GAMMA = 6.0
_GAMMA_SEARCH_STEPS = 20


class ImageProcessingError(RuntimeError):
    """The generated data could not be read as an image."""


def to_wallpaper(raw: bytes, width: int, height: int, moon: Moon | None = None) -> bytes:
    try:
        with Image.open(io.BytesIO(raw)) as source:
            image = source.convert("L")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageProcessingError("generated data is not a valid image") from exc

    blank_height = round(height * TOP_BLANK_RATIO)
    picture = _darken(_cover_fit(_trim_edges(image), width, height - blank_height))
    canvas = _blank_canvas(picture, width, height, round(height * TOP_FADE_RATIO))
    canvas.paste(picture, (0, blank_height), _fade_mask(picture, round(height * TOP_FADE_RATIO)))
    if moon is not None:
        paint_moon(canvas, moon)

    # Saved as 3-channel JPEG (neutral chroma costs almost nothing) for maximum iOS compatibility.
    output = io.BytesIO()
    canvas.convert("RGB").save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return output.getvalue()


def _trim_edges(image: Image.Image) -> Image.Image:
    margin_x, margin_y = round(image.width * EDGE_TRIM_RATIO), round(image.height * EDGE_TRIM_RATIO)
    return image.crop((margin_x, margin_y, image.width - margin_x, image.height - margin_y))


def _cover_fit(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize(
        (max(width, round(image.width * scale)), max(height, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _darken(image: Image.Image) -> Image.Image:
    """Apply the weakest gamma that brings the mean brightness down to the ceiling.

    A gamma curve keeps pure white white, so a bright moon survives the darkening.
    """
    histogram = image.histogram()
    pixels = sum(histogram)

    def mean_with(gamma: float) -> float:
        return (
            sum(count * _gamma_level(level, gamma) for level, count in enumerate(histogram))
            / pixels
        )

    if mean_with(1.0) <= MAX_MEAN_BRIGHTNESS:
        return image
    low, high = 1.0, _MAX_GAMMA
    for _ in range(_GAMMA_SEARCH_STEPS):
        middle = (low + high) / 2
        low, high = (middle, high) if mean_with(middle) > MAX_MEAN_BRIGHTNESS else (low, middle)
    return image.point([round(_gamma_level(level, high)) for level in range(256)])


def _gamma_level(level: int, gamma: float) -> float:
    return _OPAQUE * (level / _OPAQUE) ** gamma


def _blank_canvas(picture: Image.Image, width: int, height: int, band: int) -> Image.Image:
    """A canvas filled with the tone of the picture's top rows, so the blank blends into it."""
    top_band = picture.crop((0, 0, width, max(1, band)))
    return Image.new("L", (width, height), int(ImageStat.Stat(top_band).median[0]))


def _fade_mask(picture: Image.Image, fade: int) -> Image.Image:
    """Opaque everywhere except the first `fade` rows, which ramp from transparent to opaque."""
    mask = Image.new("L", picture.size, _OPAQUE)
    if fade > 0:
        mask.paste(Image.linear_gradient("L").resize((picture.width, fade)), (0, 0))
    return mask
