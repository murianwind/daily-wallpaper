from PIL import Image, ImageChops
from pytest_bdd import given, parsers, scenarios, then, when

from support import capture
from wallpaper import config, moon_painter

scenarios("features/moon_paint.feature")

SKY_LEVEL = 30
BRIGHT = 200
DARK = 110


@given("어두운 단색 캔버스", target_fixture="canvas")
def _canvas():
    return Image.new("L", (config.WALLPAPER_WIDTH, config.WALLPAPER_HEIGHT), SKY_LEVEL)


def _center(canvas, side):
    return (
        round(canvas.width * config.MOON_CENTER_X_RATIOS[side]),
        round(canvas.height * config.MOON_CENTER_Y_RATIO),
    )


def _radius(canvas):
    return round(canvas.width * config.MOON_RADIUS_RATIO)


@when(parsers.parse("{side} 쪽에 {phase} 달을 그린다"), target_fixture="painted")
def _paint(canvas, ctx, side, phase):
    ctx["side"] = side
    before = canvas.copy()
    moon_painter.paint_moon(canvas, moon_painter.Moon(phase=phase, side=side))
    return before


@when(parsers.parse("{side} 쪽에 {phase} 달을 그리려 한다"))
def _try_paint(canvas, ctx, side, phase):
    _, ctx["error"] = capture(
        moon_painter.paint_moon, canvas, moon_painter.Moon(phase=phase, side=side)
    )


@then("달 중심 픽셀은 밝다")
def _center_bright(canvas, ctx):
    assert canvas.getpixel(_center(canvas, ctx["side"])) > BRIGHT


@then("화면 가운데 같은 높이의 픽셀은 어둡다")
def _screen_center_dark(canvas):
    assert canvas.getpixel((canvas.width // 2, _center(canvas, "left")[1])) < DARK


@then("반대쪽 같은 높이의 픽셀은 어둡다")
def _opposite_dark(canvas, ctx):
    other = "left" if ctx["side"] == "right" else "right"
    assert canvas.getpixel(_center(canvas, other)) < DARK


def _sample(canvas, ctx, offset_ratio, direction):
    x, y = _center(canvas, ctx["side"])
    return canvas.getpixel((x + direction * round(_radius(canvas) * offset_ratio), y))


def _check(level, state):
    assert (level > BRIGHT) if state == "밝다" else (level < DARK)


@then(parsers.parse("달 중심에서 오른쪽으로 {ratio:f} 반지름 지점은 {state}"))
def _right_sample(canvas, ctx, ratio, state):
    _check(_sample(canvas, ctx, ratio, +1), state)


@then(parsers.parse("달 중심에서 왼쪽으로 {ratio:f} 반지름 지점은 {state}"))
def _left_sample(canvas, ctx, ratio, state):
    _check(_sample(canvas, ctx, ratio, -1), state)


@then("캔버스는 바뀌지 않았다")
def _unchanged(canvas, painted):
    assert ImageChops.difference(canvas, painted).getbbox() is None


@then("달 입력 오류가 발생한다")
def _error(ctx):
    assert isinstance(ctx["error"], ValueError)
