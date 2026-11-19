import json
import random

from pytest_bdd import given, parsers, scenarios, then, when

from support import capture
from wallpaper import spot_selector
from wallpaper.spot_selector import Spot, SpotDataError

scenarios("features/spot_selection.feature")

WINDOW = 20  # 40 spots in data/spots.json -> half of them are remembered


def _spot(index):
    return Spot(id=f"s{index}", name_ko=f"곳{index}", area="x", visual="v")


def _write(tmp_path, items):
    path = tmp_path / "spots.json"
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return path


@given("명승지가 1곳뿐인 목록", target_fixture="spots")
def _single_spot():
    return [_spot(1)]


@given("명승지가 2곳뿐인 목록", target_fixture="spots")
def _two_spots():
    return [_spot(1), _spot(2)]


@given("visual 항목이 빠진 명승지 파일", target_fixture="bad_file")
def _missing_visual(tmp_path):
    return _write(tmp_path, [{"id": "a", "name_ko": "가", "area": "x"}])


@given("id가 중복된 명승지 파일", target_fixture="bad_file")
def _duplicate_id(tmp_path):
    item = {"id": "a", "name_ko": "가", "area": "x", "visual": "v"}
    return _write(tmp_path, [item, dict(item)])


@given("최근 기록이 비어 있다", target_fixture="recent")
def _no_recent():
    return []


@given(parsers.parse("최근 기록이 목록의 앞쪽 {count:d}곳이다"), target_fixture="recent")
def _first_n_recent(spots, count):
    return [spot.id for spot in spots[:count]]


@given(parsers.parse('최근 기록이 "{spot_id}" 하나뿐이다'), target_fixture="recent")
def _unknown_recent(spot_id):
    return [spot_id]


@given("최근 기록이 첫 번째 명승지 하나뿐이다", target_fixture="recent")
def _first_recent(spots):
    return [spots[0].id]


@when(parsers.parse("같은 난수 발생기로 {times:d}번 연달아 고른다"), target_fixture="picks")
def _pick_many(spots, recent, times):
    rng = random.Random(0)
    return [spot_selector.choose_spot(spots, recent, rng) for _ in range(times)]


@when(parsers.parse("난수 시드 {seed:d} 로 두 번 고른다"), target_fixture="twice")
def _pick_twice(spots, recent, seed):
    return (
        spot_selector.choose_spot(spots, recent, random.Random(seed)),
        spot_selector.choose_spot(spots, recent, random.Random(seed)),
    )


@when("명승지를 한 번 고르려 한다")
def _try_pick(spots, recent, ctx):
    _, ctx["error"] = capture(spot_selector.choose_spot, spots, recent, random.Random(0))


@when("그 파일을 불러오려 한다")
def _try_load(bad_file, ctx):
    _, ctx["error"] = capture(spot_selector.load_spots, bad_file)


@then("명승지가 2곳 이상 있다")
def _at_least_two(spots):
    assert len(spots) >= 2


@then("최근 기록에 있는 명승지는 한 번도 나오지 않는다")
def _recent_never_picked(picks, recent):
    assert not {spot.id for spot in picks} & set(recent)


@then("모든 명승지가 한 번 이상 나온다")
def _all_picked(picks, spots):
    assert {spot.id for spot in picks} == {spot.id for spot in spots}


@then("기록의 앞쪽 20곳은 나오지 않고 21번째부터는 나온다")
def _only_window_avoided(picks, recent):
    picked = {spot.id for spot in picks}
    assert not picked & set(recent[:WINDOW])
    assert picked & set(recent[WINDOW:])


@then("100번 모두 명승지가 골라진다")
def _all_hundred(picks):
    assert len(picks) == 100


@then("두 결과가 같다")
def _same(twice):
    assert twice[0] == twice[1]


@then("명승지 부족 오류가 발생한다")
def _not_enough(ctx):
    assert isinstance(ctx["error"], SpotDataError)


@then(parsers.parse('데이터 오류가 발생하고 메시지에 "{word}"이 들어 있다'))
@then(parsers.parse('데이터 오류가 발생하고 메시지에 "{word}"가 들어 있다'))
def _data_error(ctx, word):
    assert isinstance(ctx["error"], SpotDataError)
    assert word in str(ctx["error"])
