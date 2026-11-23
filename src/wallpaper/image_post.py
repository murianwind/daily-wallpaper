"""Turn the raw generated image into an iPhone-sized grayscale JPEG.

The picture is trimmed and fitted into the lower part of the screen. If it is too bright (so iOS
would show dark text) its tones are compressed to a dark range, keeping detail. The top third is a
blank sky made from the picture's own top band mirrored upwards (so clouds keep their shapes),
blurred and dimmed towards the top. Rain or snow is painted over everything, then the moon, so the
darkening does not dim them.
"""

import io

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

from .config import (
    EDGE_TRIM_RATIO,
    MAX_MEAN_BRIGHTNESS,
    MIN_BLACK_LEVEL,
    SKY_BAND_RATIO,
    SKY_MAX_BLUR,
    TOP_BLANK_RATIO,
    TOP_DIM_RATIO,
)
from .moon_painter import Moon, paint_moon
from .precipitation import Precipitation, paint_precipitation

JPEG_QUALITY = 92
_OPAQUE = 255


class ImageProcessingError(RuntimeError):
    """The generated data could not be read as an image."""


def to_wallpaper(
    raw: bytes,
    width: int,
    height: int,
    moon: Moon | None = None,
    precipitation: Precipitation | None = None,
) -> bytes:
    try:
        with Image.open(io.BytesIO(raw)) as source:
            image = source.convert("L")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageProcessingError("generated data is not a valid image") from exc

    blank_height = round(height * TOP_BLANK_RATIO)
    band = round(height * SKY_BAND_RATIO)
    picture = _compress_tones(_cover_fit(_trim_edges(image), width, height - blank_height))

    canvas = Image.new("L", (width, height))
    canvas.paste(_sky(picture, blank_height, band), (0, 0))
    canvas.paste(picture, (0, blank_height))
    if precipitation is not None:
        paint_precipitation(canvas, precipitation)
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


def _sky(picture: Image.Image, blank_height: int, band: int) -> Image.Image:
    """The `blank_height` rows above the picture.

    The picture's top `band` rows are mirrored upwards, alternating flipped and unflipped copies so
    every join is seamless and the sky continues the picture's own clouds. It is blurred more and
    more towards the top and dimmed there, so the repetition fades out instead of showing.
    """
    strip = picture.crop((0, 0, picture.width, max(1, band)))
    sky = Image.new("L", (picture.width, blank_height))
    flipped = ImageOps.flip(strip)
    for index in range(-(-blank_height // strip.height)):
        tile = flipped if index % 2 == 0 else strip
        sky.paste(tile, (0, blank_height - (index + 1) * strip.height))

    blur_weight = ImageOps.flip(Image.linear_gradient("L").resize((picture.width, blank_height)))
    sky = Image.composite(sky.filter(ImageFilter.GaussianBlur(SKY_MAX_BLUR)), sky, blur_weight)

    ramp = Image.linear_gradient("L").resize((picture.width, blank_height))
    dimming = ramp.point(
        lambda v: round(_OPAQUE * (TOP_DIM_RATIO + (1 - TOP_DIM_RATIO) * v / _OPAQUE))
    )
    return ImageChops.multiply(sky, dimming)
