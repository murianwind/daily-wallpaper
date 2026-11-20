import io

from PIL import Image
from pytest_bdd import given, parsers, scenarios, then, when

from support import capture, png_bytes
from wallpaper import config, image_post

scenarios("features/image.feature")

BROWN = (120, 90, 60)


@given(parsers.parse("{width:d}x{height:d} PNG 이미지"), target_fixture="raw")
def _plain(width, height):
    return png_bytes(width, height)


@given("가로 3등분(빨강, 초록, 파랑)된 1200x400 PNG 이미지", target_fixture="raw")
def _three_bands():
    image = Image.new("RGB", (1200, 400))
    for index, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        image.paste(color, (index * 400, 0, (index + 1) * 400, 400))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given("갈색 단색 PNG 이미지", target_fixture="raw")
def _brown():
    return png_bytes(300, 600, color=BROWN)


@given("사방에 6% 두께의 흰 테두리가 있는 검은색 880x1920 PNG 이미지", target_fixture="raw")
def _framed():
    width, height = 880, 1920
    image = Image.new("L", (width, height), 255)
    image.paste(
        0,
        (
            round(width * 0.06),
            round(height * 0.06),
            width - round(width * 0.06),
            height - round(height * 0.06),
        ),
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given("왼쪽은 검은색 오른쪽은 흰색인 1104x1600 PNG 이미지", target_fixture="raw")
def _half_black_half_white():
    image = Image.new("L", (1104, 1600), 255)
    image.paste(0, (0, 0, 552, 1600))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given("투명 배경 RGBA PNG 이미지", target_fixture="raw")
def _transparent():
    return png_bytes(300, 600, color=(10, 20, 30, 0), mode="RGBA")


@given("이미지가 아닌 바이트", target_fixture="raw")
def _not_an_image():
    return b"definitely not an image"


@when(parsers.parse("{width:d}x{height:d} 크기로 변환한다"))
def _convert(raw, ctx, width, height):
    ctx["result"], ctx["error"] = capture(image_post.to_wallpaper, raw, width, height)


@then(parsers.parse("결과는 {width:d}x{height:d} JPEG 이다"))
def _is_jpeg(ctx, width, height):
    assert ctx["error"] is None
    with Image.open(io.BytesIO(ctx["result"])) as image:
        assert image.format == "JPEG"
        assert image.size == (width, height)


def _luma(red, green, blue):
    """ITU-R BT.601 luma, the same weighting Pillow uses for RGB -> L."""
    return 0.299 * red + 0.587 * green + 0.114 * blue


def _pixel(ctx, x_ratio, y_ratio):
    with Image.open(io.BytesIO(ctx["result"])) as image:
        rgb = image.convert("RGB")
        return rgb.getpixel((int(rgb.width * x_ratio), int(rgb.height * y_ratio)))


def _assert_gray_level(pixel, expected):
    assert max(pixel) - min(pixel) <= 2
    assert abs(pixel[0] - expected) <= 4


@then("결과의 가운데 픽셀은 초록색의 밝기이다")
def _center_is_green_level(ctx):
    _assert_gray_level(_pixel(ctx, 0.5, 0.5), _luma(0, 255, 0))


@then("결과의 가운데 픽셀은 갈색의 밝기이다")
def _center_is_brown_level(ctx):
    _assert_gray_level(_pixel(ctx, 0.5, 0.5), _luma(*BROWN))


@then("결과의 가장자리 표본 픽셀에는 테두리의 흰색이 없다")
def _edges_have_no_frame(ctx):
    for x_ratio in (0.0, 0.5, 0.999):
        for y_ratio in (0.0, 0.5, 0.999):
            assert _pixel(ctx, x_ratio, y_ratio)[0] < 60


def _gray(ctx, x_ratio, y_ratio):
    return _pixel(ctx, x_ratio, y_ratio)[0]


@then("결과의 위쪽 3분의 1 표본 픽셀은 모두 같은 밝기이다")
def _top_third_blank(ctx):
    levels = {
        _gray(ctx, x_ratio, y_ratio)
        for x_ratio in (0.05, 0.25, 0.5, 0.75, 0.95)
        for y_ratio in (0.02, 0.15, 0.3)
    }
    assert max(levels) - min(levels) <= 2


@then("결과의 아래쪽 표본에서 왼쪽은 검고 오른쪽은 밝다")
def _lower_part_has_picture(ctx):
    for y_ratio in (0.6, 0.8, 0.98):
        assert _gray(ctx, 0.25, y_ratio) < 40
        assert _gray(ctx, 0.75, y_ratio) > 215


@then("결과의 경계 바로 아래 왼쪽 픽셀은 빈 배경과 거의 같은 밝기이다")
def _seam_is_soft(ctx):
    blank = _gray(ctx, 0.25, 0.1)
    just_below = _gray(ctx, 0.25, config.TOP_BLANK_RATIO + 0.002)
    assert abs(just_below - blank) <= 30


@then("결과의 경계에서 충분히 내려간 왼쪽 픽셀은 검다")
def _picture_resumes(ctx):
    assert _gray(ctx, 0.25, config.TOP_BLANK_RATIO + config.TOP_FADE_RATIO + 0.03) < 40


@then("결과의 모든 표본 픽셀은 회색이다")
def _samples_are_gray(ctx):
    for x_ratio in (0.1, 0.5, 0.9):
        for y_ratio in (0.1, 0.5, 0.9):
            red, green, blue = _pixel(ctx, x_ratio, y_ratio)
            assert max(red, green, blue) - min(red, green, blue) <= 2


@then("이미지 처리 오류가 발생한다")
def _processing_error(ctx):
    assert isinstance(ctx["error"], image_post.ImageProcessingError)
