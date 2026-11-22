from datetime import UTC, date, datetime, timedelta

from pytest_bdd import parsers, scenarios, then, when

from support import capture
from wallpaper import moon_phase
from wallpaper.config import KST

scenarios("features/moon.feature")


def _kst(day, hour, minute):
    parsed = date.fromisoformat(day)
    return datetime(parsed.year, parsed.month, parsed.day, hour, minute, tzinfo=KST)


@when(
    parsers.parse("한국 시각 {day} {hour:d}시 {minute:d}분 의 달 모양을 구한다"),
    target_fixture="phase",
)
def _phase(day, hour, minute):
    return moon_phase.phase_of(_kst(day, hour, minute))


@then(parsers.parse('달 모양은 "{expected}" 이다'))
def _phase_is(phase, expected):
    assert phase == expected


@when(
    parsers.parse(
        "한국 시각 {day} {hour:d}시 {minute:d}분 과 같은 순간의 세계시로 달 모양을 구한다"
    ),
    target_fixture="phases",
)
def _both_zones(day, hour, minute):
    moment = _kst(day, hour, minute)
    utc = moment.astimezone(UTC)
    assert utc.utcoffset() == timedelta(0)
    return moon_phase.phase_of(moment), moon_phase.phase_of(utc)


@then("두 달 모양은 같다")
def _same(phases):
    assert phases[0] == phases[1]


@when("시간대 정보가 없는 시각의 달 모양을 구하려 한다")
def _naive(ctx):
    _, ctx["error"] = capture(moon_phase.phase_of, datetime(2026, 11, 24, 16, 10))  # noqa: DTZ001 - naive on purpose


@then("달 모양 입력 오류가 발생한다")
def _error(ctx):
    assert isinstance(ctx["error"], ValueError)
