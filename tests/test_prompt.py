import re
from datetime import date

from pytest_bdd import given, parsers, scenarios, then, when

from support import capture
from wallpaper import prompt_builder, weather
from wallpaper.config import SKY_SIDES, SLOTS
from wallpaper.spot_selector import Spot

scenarios("features/prompt.feature")

DEFAULT_SIDE = SKY_SIDES[0]

# Whole words only, so e.g. "layered" is not mistaken for "red".
COLOR_NAMES = re.compile(
    r"\b(red|green|blue|yellow|orange|pink|purple|violet|gold|golden|ochre|russet|indigo|"
    r"crimson|scarlet|azure|turquoise|brown|amber)\b",
    re.IGNORECASE,
)


def _all_conditions():
    """Every condition weather.classify can produce, one label each."""
    labels = ["맑음", "구름많음", "흐림", "비", "눈", "안개", "뇌우", "황사"]
    return {weather.classify(label) for label in labels}


def _all_seasons():
    return {prompt_builder.season_of(date(2026, month, 1)) for month in range(1, 13)}


@given("박연폭포 명승지", target_fixture="spot")
def _bakyeon():
    return Spot(
        id="bakyeon",
        name_ko="박연폭포",
        area="개성",
        visual="a tall narrow waterfall plunging from a granite cliff into a deep pool",
        waterfall=True,
    )


@given("비로봉 명승지", target_fixture="spot")
def _birobong():
    return Spot(
        id="birobong",
        name_ko="비로봉",
        area="금강산",
        visual="a steep bare granite peak with jagged ridges",
    )


@when(parsers.parse("날짜 {day} 의 계절을 구한다"), target_fixture="season")
def _season(day):
    return prompt_builder.season_of(date.fromisoformat(day))


@then(parsers.parse('계절은 "{expected}" 이다'))
def _season_is(season, expected):
    assert season == expected


@when(
    parsers.parse("{slot} 시간대, {season} 계절, {condition} 날씨로 프롬프트를 만든다"),
    target_fixture="prompt",
)
def _build(spot, slot, season, condition):
    return prompt_builder.build_prompt(spot, slot, season, condition, DEFAULT_SIDE)


@when(
    parsers.parse(
        "{slot} 시간대, {season} 계절, {condition} 날씨, {side} 쪽 물줄기로 프롬프트를 만든다"
    ),
    target_fixture="prompt",
)
def _build_with_side(spot, slot, season, condition, side):
    return prompt_builder.build_prompt(spot, slot, season, condition, side)


@when(
    parsers.parse(
        "{slot} 시간대, {season} 계절, {condition} 날씨, {side} 쪽 물줄기로 프롬프트를 만들려 한다"
    )
)
def _try_build_with_side(spot, ctx, slot, season, condition, side):
    _, ctx["error"] = capture(prompt_builder.build_prompt, spot, slot, season, condition, side)


@when(parsers.parse("{slot} 시간대, {season} 계절, {condition} 날씨로 프롬프트를 만들려 한다"))
def _try_build(spot, ctx, slot, season, condition):
    _, ctx["error"] = capture(
        prompt_builder.build_prompt, spot, slot, season, condition, DEFAULT_SIDE
    )


@then(parsers.parse('프롬프트에 "{text}" 가 들어 있다'))
def _contains(prompt, text):
    assert text in prompt


@then(parsers.parse('프롬프트에 "{text}" 가 들어 있지 않다'))
def _not_contains(prompt, text):
    assert text not in prompt


@then("모든 조합으로 프롬프트를 만들 수 있다")
def _all_combinations(spot):
    for slot in SLOTS:
        for season in _all_seasons():
            for condition in _all_conditions():
                assert prompt_builder.build_prompt(spot, slot, season, condition, DEFAULT_SIDE)


def _every_prompt(spots):
    return [
        prompt_builder.build_prompt(spot, slot, season, condition, side)
        for spot in spots
        for slot in SLOTS
        for season in _all_seasons()
        for condition in _all_conditions()
        for side in SKY_SIDES
    ]


@then("모든 명승지와 조합의 프롬프트가 2000자 이하이다")
def _length_limit(spots):
    assert max(len(prompt) for prompt in _every_prompt(spots)) <= 2000


@then("모든 명승지와 조합의 프롬프트에 색 이름이 없다")
def _no_color_names(spots):
    for prompt in _every_prompt(spots):
        assert not COLOR_NAMES.search(prompt), COLOR_NAMES.search(prompt).group()


@then("프롬프트 입력 오류가 발생한다")
def _input_error(ctx):
    assert isinstance(ctx["error"], ValueError)
