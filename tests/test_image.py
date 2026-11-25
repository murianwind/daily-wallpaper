import io

from PIL import Image, ImageStat
from pytest_bdd import given, parsers, scenarios, then, when

from support import capture, png_bytes
from wallpaper import config, image_post, moon_painter

scenarios("features/image.feature")

BROWN = (70, 50, 30)
GREEN = (0, 80, 0)
DARK_GRAY = 40


@given(parsers.parse("{width:d}x{height:d} PNG 이미지"), target_fixture="raw")
def _plain(width, height):
    return png_bytes(width, height)


@given("가로 3등분(빨강, 초록, 파랑)된 1200x400 PNG 이미지", target_fixture="raw")
def _three_bands():
    image = Image.new("RGB", (1200, 400))
    for index, color in enumerate([(90, 0, 0), GREEN, (0, 0, 90)]):
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


@given("밝은 회색 단색 1104x1600 PNG 이미지", target_fixture="raw")
def _bright_gray():
    return png_bytes(1104, 1600, color=190, mode="L")


@given("어두운 회색 단색 1104x1600 PNG 이미지", target_fixture="raw")
def _dark_gray():
    return png_bytes(1104, 1600, color=DARK_GRAY, mode="L")


@given("위쪽에서 아래로 점점 밝아지는 1104x1600 PNG 이미지", target_fixture="raw")
def _brightening_downwards():
    image = Image.new("L", (1104, 1600), 230)
    ramp = Image.linear_gradient("L").resize((1104, 400)).point(lambda v: 60 + round(v * 0.66))
    image.paste(ramp, (0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given(
    "위쪽 하늘 아래로 왼쪽에 가느다란 어두운 봉우리가 솟은 1104x1600 PNG 이미지",
    target_fixture="raw",
)
def _peak_under_sky():
    image = Image.new("L", (1104, 1600), 190)
    image.paste(50, (100, 250, 112, 1600))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given("하늘 윗부분에 작은 어두운 점이 있는 1104x1600 PNG 이미지", target_fixture="raw")
def _speck_in_sky():
    image = Image.new("L", (1104, 1600), 190)
    image.paste(60, (400, 160, 408, 168))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given("종이 결이 있는 회색 하늘 1104x1600 PNG 이미지", target_fixture="raw")
def _grainy_sky():
    buffer = io.BytesIO()
    Image.effect_noise((1104, 1600), 14).save(buffer, format="PNG")
    return buffer.getvalue()


@given("어두운 하늘 위쪽에 나무가 솟은 1104x1600 PNG 이미지", target_fixture="raw")
def _tree_in_dark_sky():
    image = Image.new("L", (1104, 1600), 30)
    image.paste(4, (100, 200, 140, 1600))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given(
    "맨 윗줄까지 가느다란 어두운 가지가 지나가는 밝은 하늘 1104x1600 PNG 이미지",
    target_fixture="raw",
)
def _twig_in_sky():
    image = Image.new("L", (1104, 1600), 150)
    image.paste(20, (500, 0, 508, 1600))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@given("왼쪽 위 모서리에 어두운 나무가 걸린 밝은 하늘 1104x1600 PNG 이미지", target_fixture="raw")
def _tree_in_corner():
    image = Image.new("L", (1104, 1600), 150)
    image.paste(20, (0, 0, 220, 700))
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
    _assert_gray_level(_pixel(ctx, 0.5, 0.5), _luma(*GREEN))


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


@when(parsers.parse("{width:d}x{height:d} 크기로 {side} 쪽 {phase} 달과 함께 변환한다"))
def _convert_with_moon(raw, ctx, width, height, side, phase):
    moon = moon_painter.Moon(phase=phase, side=side)
    ctx["result"], ctx["error"] = capture(image_post.to_wallpaper, raw, width, height, moon)


def _moon_spot(ctx, side="right"):
    return _gray(ctx, config.MOON_CENTER_X_RATIOS[side], config.MOON_CENTER_Y_RATIO)


@then("결과의 달 자리는 밝다")
def _moon_spot_bright(ctx):
    assert _moon_spot(ctx) > 200


@then("결과의 달 자리는 밝지 않다")
def _moon_spot_not_bright(ctx):
    assert _moon_spot(ctx) < 150


def _row(ctx, y_ratio):
    return [_gray(ctx, x_ratio, y_ratio) for x_ratio in (0.05, 0.25, 0.5, 0.75, 0.95)]


@then("결과의 빈 영역은 그림의 하늘만큼 밝다")
def _blank_as_bright_as_sky(ctx):
    assert _gray(ctx, 0.5, 0.30) >= 0.85 * _gray(ctx, 0.9, 0.45)


@then("결과의 빈 영역과 그림의 경계 위아래 밝기는 거의 같다")
def _striped_boundary_continuous(ctx):
    boundary = config.TOP_BLANK_RATIO
    assert abs(_gray(ctx, 0.5, boundary - 0.0008) - _gray(ctx, 0.5, boundary + 0.0008)) <= 12


@then("결과의 빈 영역은 봉우리 위쪽에서도 좌우가 비슷한 하늘이다")
def _no_mirrored_peak(ctx):
    for y_ratio in (0.03, 0.08, 0.14, 0.2, 0.26, 0.31):
        assert _gray(ctx, 0.03, y_ratio) >= 0.85 * _gray(ctx, 0.9, y_ratio)


@then("결과의 빈 영역은 각 줄이 가로로 고르다")
def _blank_rows_even(ctx):
    with Image.open(io.BytesIO(ctx["result"])) as image:
        gray = image.convert("L")
        for y in range(0, round(gray.height * config.TOP_BLANK_RATIO), 3):
            low, high = gray.crop((0, y, gray.width, y + 1)).getextrema()
            assert high - low <= 5


@then("결과의 경계 위아래 결의 세기는 거의 같다")
def _grain_continuous(ctx):
    boundary = round(config.WALLPAPER_HEIGHT * config.TOP_BLANK_RATIO)
    with Image.open(io.BytesIO(ctx["result"])) as image:
        gray = image.convert("L")
        above = ImageStat.Stat(gray.crop((0, boundary - 20, gray.width, boundary))).stddev[0]
        below = ImageStat.Stat(gray.crop((0, boundary, gray.width, boundary + 20))).stddev[0]
    assert abs(above - below) <= 4


@then("결과의 맨 위 픽셀은 빈 영역 아래쪽 픽셀보다 어둡다")
def _top_is_darker(ctx):
    assert _gray(ctx, 0.5, 0.005) + 10 <= _gray(ctx, 0.5, config.TOP_BLANK_RATIO - 0.01)


@then("결과의 빈 영역 아래쪽과 그림 하늘의 밝기는 거의 같다")
def _no_seam(ctx):
    above = _gray(ctx, 0.5, config.TOP_BLANK_RATIO - 0.004)
    below = _gray(ctx, 0.5, config.TOP_BLANK_RATIO + config.TOP_FADE_RATIO + 0.01)
    assert abs(above - below) <= 6


@then("결과의 아래쪽 표본에서 오른쪽은 왼쪽보다 훨씬 밝다")
def _picture_contrast_kept(ctx):
    for y_ratio in (0.6, 0.8, 0.98):
        assert _gray(ctx, 0.75, y_ratio) >= _gray(ctx, 0.25, y_ratio) + 60


@then("결과의 아래쪽 왼쪽 표본은 최소 검정 밝기 이상이다")
def _blacks_not_crushed(ctx):
    for y_ratio in (0.6, 0.8, 0.98):
        assert _gray(ctx, 0.25, y_ratio) >= config.MIN_BLACK_LEVEL - 2


@then("결과 전체의 평균 밝기는 상한 이하이다")
def _mean_below_ceiling(ctx):
    with Image.open(io.BytesIO(ctx["result"])) as image:
        assert ImageStat.Stat(image.convert("L")).mean[0] <= config.MAX_MEAN_BRIGHTNESS + 2


@then("결과 전체의 평균 밝기는 상한 근처이다")
def _mean_near_ceiling(ctx):
    with Image.open(io.BytesIO(ctx["result"])) as image:
        mean = ImageStat.Stat(image.convert("L")).mean[0]
    assert config.MAX_MEAN_BRIGHTNESS - 12 <= mean <= config.MAX_MEAN_BRIGHTNESS + 2


@then("결과의 가운데 픽셀은 어두운 회색의 밝기이다")
def _center_is_dark_gray(ctx):
    _assert_gray_level(_pixel(ctx, 0.5, 0.5), DARK_GRAY)


@then("결과의 모든 표본 픽셀은 회색이다")
def _samples_are_gray(ctx):
    for x_ratio in (0.1, 0.5, 0.9):
        for y_ratio in (0.1, 0.5, 0.9):
            red, green, blue = _pixel(ctx, x_ratio, y_ratio)
            assert max(red, green, blue) - min(red, green, blue) <= 2


@then("이미지 처리 오류가 발생한다")
def _processing_error(ctx):
    assert isinstance(ctx["error"], image_post.ImageProcessingError)
