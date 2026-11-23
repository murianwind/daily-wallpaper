from PIL import Image, ImageChops, ImageStat
from pytest_bdd import given, parsers, scenarios, then, when

from support import capture
from wallpaper import config, precipitation

scenarios("features/precipitation.feature")

BASE_LEVEL = 40
BRIGHTER_BY = 20


@given("어두운 단색 캔버스", target_fixture="canvas")
def _canvas():
    return Image.new("L", (config.WALLPAPER_WIDTH, config.WALLPAPER_HEIGHT), BASE_LEVEL)


@when(parsers.parse('날씨 "{condition}" 의 강수를 정한다'), target_fixture="decided")
def _decide(condition):
    return precipitation.precipitation_for(condition, seed=1)


@then(parsers.parse('강수 종류는 "{kind}" 이다'))
def _kind_is(decided, kind):
    assert (decided.kind if decided else "없음") == kind


@when(parsers.parse("{kind} 를 그린다"), target_fixture="before")
def _paint(canvas, kind):
    before = canvas.copy()
    precipitation.paint_precipitation(canvas, precipitation.Precipitation(kind, seed=0))
    return before


def _bright_mask(canvas):
    return canvas.point(lambda value: 255 if value >= BASE_LEVEL + BRIGHTER_BY else 0)


def _bright_ratio(canvas, top=0.0, bottom=1.0):
    height = canvas.height
    part = _bright_mask(canvas).crop((0, round(height * top), canvas.width, round(height * bottom)))
    return ImageStat.Stat(part).mean[0] / 255


@then("위쪽과 가운데와 아래쪽 모두에 밝은 점이 있다")
def _spread_everywhere(canvas):
    for top, bottom in ((0.0, 0.33), (0.33, 0.66), (0.66, 1.0)):
        assert _bright_ratio(canvas, top, bottom) > 0.001


@then("밝은 점의 비율은 화면의 일부분에 그친다")
def _only_part_of_screen(canvas):
    assert 0.001 < _bright_ratio(canvas) < 0.25


@then("평균 밝기는 조금만 올라간다")
def _mean_barely_rises(canvas, before):
    rise = ImageStat.Stat(canvas).mean[0] - ImageStat.Stat(before).mean[0]
    assert 0 < rise <= 8


def _mean_run(mask, vertical):
    """Average length of the bright runs along columns (vertical) or rows, in a 300x300 sample."""
    sample = mask.crop((400, 800, 700, 1100))
    lines = [
        [sample.getpixel((x, y) if vertical else (y, x)) for y in range(sample.height)]
        for x in range(sample.width)
    ]
    runs, current = [], 0
    for line in lines:
        for value in [*line, 0]:
            if value:
                current += 1
            elif current:
                runs.append(current)
                current = 0
    return sum(runs) / len(runs)


@then("밝은 점들은 가로보다 세로로 길게 이어진다")
def _streaks_are_vertical(canvas):
    mask = _bright_mask(canvas)
    assert _mean_run(mask, vertical=True) >= 2 * _mean_run(mask, vertical=False)


def _paint_with_seed(seed, kind="rain"):
    canvas = Image.new("L", (config.WALLPAPER_WIDTH, config.WALLPAPER_HEIGHT), BASE_LEVEL)
    precipitation.paint_precipitation(canvas, precipitation.Precipitation(kind, seed))
    return canvas


@when(parsers.parse("시드 {seed:d} 로 {kind} 을 두 번 그린다"), target_fixture="pair")
def _twice(seed, kind):
    return _paint_with_seed(seed, kind), _paint_with_seed(seed, kind)


@when(parsers.parse("시드 {first:d} 과 시드 {second:d} 로 {kind} 을 그린다"), target_fixture="pair")
def _two_seeds(first, second, kind):
    return _paint_with_seed(first, kind), _paint_with_seed(second, kind)


@then("두 결과는 같다")
def _same(pair):
    assert ImageChops.difference(*pair).getbbox() is None


@then("두 결과는 다르다")
def _different(pair):
    assert ImageChops.difference(*pair).getbbox() is not None


@when(parsers.parse("{kind} 를 그리려 한다"))
def _try_paint(canvas, ctx, kind):
    _, ctx["error"] = capture(
        precipitation.paint_precipitation, canvas, precipitation.Precipitation(kind, seed=0)
    )


@then("알 수 없는 강수 종류 오류가 발생한다")
def _unknown_kind(ctx):
    assert isinstance(ctx["error"], ValueError)
