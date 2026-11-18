import json
from datetime import date, timedelta

from pytest_bdd import given, parsers, scenarios, then, when

from support import capture
from wallpaper import spot_selector
from wallpaper.spot_selector import Spot, SpotDataError

scenarios("features/spot_selection.feature")


def _spot(index):
    return Spot(id=f"s{index}", name_ko=f"곳{index}", area="x", visual="v")


def _write(tmp_path, items):
    path = tmp_path / "spots.json"
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return path


@given("명승지가 1곳뿐인 목록", target_fixture="spots")
def _single_spot():
    return [_spot(1)]


@given("visual 항목이 빠진 명승지 파일", target_fixture="bad_file")
def _missing_visual(tmp_path):
    return _write(tmp_path, [{"id": "a", "name_ko": "가", "area": "x"}])


@given("id가 중복된 명승지 파일", target_fixture="bad_file")
def _duplicate_id(tmp_path):
    item = {"id": "a", "name_ko": "가", "area": "x", "visual": "v"}
    return _write(tmp_path, [item, dict(item)])


@when(
    parsers.parse("{start}부터 {days:d}일 동안 매일 낮과 밤의 명승지를 고른다"),
    target_fixture="picks",
)
def _pick_range(spots, start, days):
    first = date.fromisoformat(start)
    return _pick_days(spots, [first + timedelta(days=i) for i in range(days)])


@when(
    parsers.parse("{start} 이후 처음 시작되는 한 주기 동안 매일 낮과 밤의 명승지를 고른다"),
    target_fixture="picks",
)
def _pick_one_cycle(spots, start):
    length = spot_selector.cycle_length(spots)
    first = date.fromisoformat(start)
    while first.toordinal() % length:
        first += timedelta(days=1)
    return _pick_days(spots, [first + timedelta(days=i) for i in range(length)])


def _pick_days(spots, days):
    return [
        (
            day,
            spot_selector.select_spot(spots, day, "day"),
            spot_selector.select_spot(spots, day, "night"),
        )
        for day in days
    ]


@when(parsers.parse("{day} 낮의 명승지를 두 번 고른다"), target_fixture="twice")
def _pick_twice(spots, day):
    target = date.fromisoformat(day)
    return (
        spot_selector.select_spot(spots, target, "day"),
        spot_selector.select_spot(spots, target, "day"),
    )


@when(parsers.parse("{day} 낮의 명승지를 고르려 한다"))
def _try_pick_day(spots, ctx, day):
    _, ctx["error"] = capture(spot_selector.select_spot, spots, date.fromisoformat(day), "day")


@when(parsers.parse("{day} 새벽의 명승지를 고르려 한다"))
def _try_pick_dawn(spots, ctx, day):
    _, ctx["error"] = capture(spot_selector.select_spot, spots, date.fromisoformat(day), "dawn")


@when("그 파일을 불러오려 한다")
def _try_load(bad_file, ctx):
    _, ctx["error"] = capture(spot_selector.load_spots, bad_file)


@then("명승지가 2곳 이상 있다")
def _at_least_two(spots):
    assert len(spots) >= 2


@then("어느 날도 낮과 밤의 명승지가 같지 않다")
def _day_night_differ(picks):
    assert all(day_spot.id != night_spot.id for _, day_spot, night_spot in picks)


@then("고른 명승지가 모두 서로 다르다")
def _all_distinct(picks):
    ids = [spot.id for _, day_spot, night_spot in picks for spot in (day_spot, night_spot)]
    assert len(ids) == len(set(ids))


@then("두 결과가 같다")
def _same(twice):
    assert twice[0] == twice[1]


@then("명승지 부족 오류가 발생한다")
def _not_enough(ctx):
    assert isinstance(ctx["error"], SpotDataError)


@then("시간대 오류가 발생한다")
def _slot_error(ctx):
    assert isinstance(ctx["error"], ValueError)
    assert "slot" in str(ctx["error"])


@then(parsers.parse('데이터 오류가 발생하고 메시지에 "{word}"이 들어 있다'))
@then(parsers.parse('데이터 오류가 발생하고 메시지에 "{word}"가 들어 있다'))
def _data_error(ctx, word):
    assert isinstance(ctx["error"], SpotDataError)
    assert word in str(ctx["error"])
