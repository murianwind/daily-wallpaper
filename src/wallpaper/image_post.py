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
    SKY_MOUNTAIN_CONTRAST,
    SKY_SPECK_SIZE,
    TOP_BLANK_RATIO,
    TOP_DIM_RATIO,
)
from .moon_painter import Moon, paint_moon
from .precipitation import Precipitation, paint_precipitation

JPEG_QUALITY = 92
_OPAQUE = 255
_SKY_SPECK_RATIO = 0.005  # a row's darkest 0.5% of pixels (ink specks in the paper) are ignored


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
    sky, overlap = _sky(picture, blank_height, band)
    canvas.paste(sky, (0, 0))
    canvas.paste(picture, (0, blank_height), _fade_mask(picture, overlap))
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


def _sky_rows(picture: Image.Image, band: int) -> int:
    """How many top rows are still sky: stop at the first row with a clearly darker part.

    Mirroring a peak or a pine into the sky would leave a symmetric dark blob up there.
    """
    darkest = [_dark_edge(picture, y) for y in range(band)]
    for y in range(1, band):
        if darkest[y] < darkest[0] - SKY_MOUNTAIN_CONTRAST:
            return y
    return band


def _dark_edge(picture: Image.Image, y: int) -> int:
    """Level below which the darkest few pixels of row `y` lie (ignores single specks)."""
    histogram = picture.crop((0, y, picture.width, y + 1)).histogram()
    allowed = picture.width * _SKY_SPECK_RATIO
    seen = 0
    for level, count in enumerate(histogram):
        seen += count
        if seen > allowed:
            return level
    return len(histogram) - 1


def _erase_specks(strip: Image.Image) -> Image.Image:
    """Remove dark and bright specks smaller than SKY_SPECK_SIZE px (big cloud shapes stay).

    Closing (grow, then shrink) fills dark specks; opening, the reverse, removes bright ones such
    as the halo that resampling leaves around a speck. Done at half size, which is much faster and
    also drops the paper grain the blurred sky does not need.
    """
    half = strip.resize((strip.width // 2, max(1, strip.height // 2)), Image.Resampling.BOX)
    size = SKY_SPECK_SIZE // 2 | 1  # the same extent at half size, kept odd
    closed = half.filter(ImageFilter.MaxFilter(size)).filter(ImageFilter.MinFilter(size))
    opened = closed.filter(ImageFilter.MinFilter(size)).filter(ImageFilter.MaxFilter(size))
    return opened.resize(strip.size, Image.Resampling.BICUBIC)


def _sky(picture: Image.Image, blank_height: int, band: int) -> tuple[Image.Image, int]:
    """The sky for the `blank_height` rows above the picture, plus `overlap` rows under its top.

    The sky rows at the picture's top (see `_sky_rows`) are mirrored upwards, alternating flipped
    and unflipped copies so every join is seamless and the sky continues the picture's own clouds.
    Small specks are erased, then it is blurred more and more towards the top and dimmed there,
    so repetition fades out. The picture later fades in over the `overlap` rows (returned too), so
    the smoothed sky does not meet the picture's paper grain in a visible line.
    """
    strip = _erase_specks(picture.crop((0, 0, picture.width, _sky_rows(picture, band))))
    sky = Image.new("L", (picture.width, blank_height + strip.height))
    sky.paste(strip, (0, blank_height))
    flipped = ImageOps.flip(strip)
    for index in range(-(-blank_height // strip.height)):
        tile = flipped if index % 2 == 0 else strip
        sky.paste(tile, (0, blank_height - (index + 1) * strip.height))

    # Blur and dim only the blank part: the overlap rows must keep the picture's own tones.
    blank = sky.crop((0, 0, picture.width, blank_height))
    blur_weight = ImageOps.flip(Image.linear_gradient("L").resize(blank.size))
    blank = Image.composite(
        blank.filter(ImageFilter.GaussianBlur(SKY_MAX_BLUR)), blank, blur_weight
    )

    ramp = Image.linear_gradient("L").resize(blank.size)
    dimming = ramp.point(
        lambda v: round(_OPAQUE * (TOP_DIM_RATIO + (1 - TOP_DIM_RATIO) * v / _OPAQUE))
    )
    sky.paste(ImageChops.multiply(blank, dimming), (0, 0))
    return sky, strip.height


def _fade_mask(picture: Image.Image, fade: int) -> Image.Image:
    """Opaque everywhere except the first `fade` rows, which ramp from transparent to opaque."""
    mask = Image.new("L", picture.size, _OPAQUE)
    mask.paste(Image.linear_gradient("L").resize((picture.width, fade)), (0, 0))
    return mask
