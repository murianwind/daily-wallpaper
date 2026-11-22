"""Turn the raw generated image into an iPhone-sized grayscale JPEG.

The picture is trimmed and fitted into the lower part of the screen. If it is too bright (so iOS
would show dark text) its tones are compressed to a dark range, keeping detail. The top third is a
blank sky that continues the picture's own sky tones and fades into it. The moon, if any, is
painted last so the darkening does not dim it.
"""

import io

from PIL import Image, ImageChops, ImageStat, UnidentifiedImageError

from .config import (
    EDGE_TRIM_RATIO,
    MAX_MEAN_BRIGHTNESS,
    MIN_BLACK_LEVEL,
    SKY_TONE_COLUMNS,
    TOP_BLANK_RATIO,
    TOP_DIM_RATIO,
    TOP_FADE_RATIO,
)
from .moon_painter import Moon, paint_moon

JPEG_QUALITY = 92
_OPAQUE = 255


class ImageProcessingError(RuntimeError):
    """The generated data could not be read as an image."""


def to_wallpaper(raw: bytes, width: int, height: int, moon: Moon | None = None) -> bytes:
    try:
        with Image.open(io.BytesIO(raw)) as source:
            image = source.convert("L")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageProcessingError("generated data is not a valid image") from exc

    blank_height = round(height * TOP_BLANK_RATIO)
    fade = round(height * TOP_FADE_RATIO)
    picture = _compress_tones(_cover_fit(_trim_edges(image), width, height - blank_height))

    canvas = Image.new("L", (width, height))
    canvas.paste(_sky(picture, blank_height, fade), (0, 0))
    canvas.paste(picture, (0, blank_height), _fade_mask(picture, fade))
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


def _compress_tones(image: Image.Image) -> Image.Image:
    """Map black..white linearly onto MIN_BLACK_LEVEL..(a level that gives the mean ceiling).

    Unlike a gamma curve this keeps the shadows apart instead of crushing them to black.
    """
    mean = ImageStat.Stat(image).mean[0]
    if mean <= MAX_MEAN_BRIGHTNESS:
        return image
    scale = (MAX_MEAN_BRIGHTNESS - MIN_BLACK_LEVEL) / mean
    return image.point([round(MIN_BLACK_LEVEL + scale * level) for level in range(256)])


def _sky(picture: Image.Image, blank_height: int, fade: int) -> Image.Image:
    """The sky above the picture (`blank_height` rows) plus `fade` rows under the picture's top.

    It repeats the picture's top-band tones, smoothly varied across the width, and gets darker
    towards the top edge, so it continues the picture's own sky instead of a separate flat block.
    """
    zones = picture.crop((0, 0, picture.width, max(1, fade))).resize(
        (SKY_TONE_COLUMNS, 1), Image.Resampling.BOX
    )
    tones = zones.resize((picture.width, 1), Image.Resampling.BICUBIC)
    sky = tones.resize((picture.width, blank_height + fade), Image.Resampling.NEAREST)

    dimming = Image.new("L", sky.size, _OPAQUE)
    ramp = Image.linear_gradient("L").resize((picture.width, blank_height))
    dimming.paste(
        ramp.point(lambda v: round(_OPAQUE * (TOP_DIM_RATIO + (1 - TOP_DIM_RATIO) * v / _OPAQUE))),
        (0, 0),
    )
    return ImageChops.multiply(sky, dimming)


def _fade_mask(picture: Image.Image, fade: int) -> Image.Image:
    """Opaque everywhere except the first `fade` rows, which ramp from transparent to opaque."""
    mask = Image.new("L", picture.size, _OPAQUE)
    if fade > 0:
        mask.paste(Image.linear_gradient("L").resize((picture.width, fade)), (0, 0))
    return mask
