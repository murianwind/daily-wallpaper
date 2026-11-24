import io

from PIL import Image, ImageStat
from pytest_bdd import given, parsers, scenarios, then, when

from wallpaper import config, image_post, sky_clouds

scenarios("features/sky_clouds.feature")

BRIGHT = 150  # uniform picture level used by the scenarios


def _convert(raw, clouds):
    return image_post.to_wallpaper(
        raw, config.WALLPAPER_WIDTH, config.WALLPAPER_HEIGHT, clouds=clouds
    )


def _gray(data):
    return Image.open(io.BytesIO(data)).convert("L")


def _blank_height():
    return round(config.WALLPAPER_HEIGHT * config.TOP_BLANK_RATIO)


def _row_variation(data):
    """Average over sampled blank rows of the brightness spread along the row."""
    image = _gray(data)
    rows = range(0, _blank_height(), 8)
    spreads = [ImageStat.Stat(image.crop((0, y, image.width, y + 1))).stddev[0] for y in rows]
    return sum(spreads) / len(spreads)


def _row_mean(data, top, bottom):
    image = _gray(data)
    return ImageStat.Stat(image.crop((0, top, image.width, bottom))).mean[0]


@given("밝은 회색 단색 1104x1600 PNG 이미지", target_fixture="raw")
def _uniform_gray():
    buffer = io.BytesIO()
    Image.new("L", (1104, 1600), BRIGHT).save(buffer, format="PNG")
    return buffer.getvalue()


@when(parsers.parse('날씨 "{condition}" 의 구름을 정한다'), target_fixture="decided")
def _decide(condition):
    return sky_clouds.clouds_for(condition, seed=1)


@then(parsers.parse("구름의 세기는 {strength:g} 이다"))
def _strength_is(decided, strength):
    assert decided.strength == strength


@when("구름 없이 변환한다", target_fixture="result")
def _without(raw):
    return _convert(raw, None)


@when(parsers.parse("세기 {strength:g} 구름으로 변환한다"), target_fixture="result")
def _with(raw, strength):
    return _convert(raw, sky_clouds.Clouds(strength, seed=0))


@when(
    parsers.parse("세기 {weak:g} 구름과 세기 {strong:g} 구름으로 각각 변환한다"),
    target_fixture="pair",
)
def _weak_and_strong(raw, weak, strong):
    return _convert(raw, sky_clouds.Clouds(weak, 0)), _convert(raw, sky_clouds.Clouds(strong, 0))


@when(parsers.parse("시드 {seed:d} 구름을 두 번 변환한다"), target_fixture="pair")
def _twice(raw, seed):
    return _convert(raw, sky_clouds.Clouds(1.0, seed)), _convert(raw, sky_clouds.Clouds(1.0, seed))


@when(
    parsers.parse("시드 {first:d} 구름과 시드 {second:d} 구름으로 각각 변환한다"),
    target_fixture="pair",
)
def _two_seeds(raw, first, second):
    return (
        _convert(raw, sky_clouds.Clouds(1.0, first)),
        _convert(raw, sky_clouds.Clouds(1.0, second)),
    )


@then("빈 영역의 가로 밝기 변화는 거의 없다")
def _flat_rows(result):
    assert _row_variation(result) < 1.5


@then("빈 영역의 가로 밝기 변화는 뚜렷하다")
def _visible_clouds(result):
    assert _row_variation(result) > 6


@then("약한 구름의 가로 밝기 변화가 더 작다")
def _weak_is_weaker(pair):
    weak, strong = pair
    assert _row_variation(weak) * 2 < _row_variation(strong)


@then("경계 위아래 밝기는 거의 같다")
def _boundary_continuous(result):
    boundary = _blank_height()
    image = _gray(result)
    middle = image.width // 2
    assert (
        abs(image.getpixel((middle, boundary - 2)) - image.getpixel((middle, boundary + 2))) <= 12
    )


@then("두 결과는 같다")
def _same(pair):
    assert pair[0] == pair[1]


@then("두 결과는 다르다")
def _different(pair):
    assert pair[0] != pair[1]


@then("맨 위쪽 줄의 평균 밝기는 경계 근처 줄의 평균 밝기보다 어둡다")
def _darker_at_top(result):
    boundary = _blank_height()
    assert _row_mean(result, 0, 40) < _row_mean(result, boundary - 40, boundary)
