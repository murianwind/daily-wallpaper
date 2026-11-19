import requests
from pytest_bdd import given, parsers, scenarios, then, when

from support import FakeResponse, Recorder
from wallpaper import history

scenarios("features/history.feature")

URL = "https://pages.test/latest.json"


def _ids(text):
    return [item.strip() for item in text.split(",")]


def _serve(payload):
    return Recorder(lambda n, *a, **k: FakeResponse(200, payload))


@given(parsers.parse('배포된 latest.json 의 최근 명승지가 "{ids}" 이다'), target_fixture="http")
def _deployed(ids):
    return _serve({"recent_spot_ids": _ids(ids)})


@given("기록 주소 요청이 연결 오류로 실패한다", target_fixture="http")
def _connection_error():
    def responder(n, *args, **kwargs):
        raise requests.ConnectionError("down")

    return Recorder(responder)


@given("기록 주소가 HTTP 404 를 돌려준다", target_fixture="http")
def _not_found():
    return Recorder(lambda n, *a, **k: FakeResponse(404))


@given("기록 주소가 JSON 이 아닌 응답을 돌려준다", target_fixture="http")
def _not_json():
    return Recorder(lambda n, *a, **k: FakeResponse(200, None, text="<html>"))


@given("기록 항목이 없는 예전 형식의 latest.json 이 배포되어 있다", target_fixture="http")
def _legacy():
    return _serve({"spot_id": "a"})


@given("기록 항목이 숫자 목록인 latest.json 이 배포되어 있다", target_fixture="http")
def _numbers():
    return _serve({"recent_spot_ids": [1, 2]})


@when("최근 명승지 기록을 읽는다", target_fixture="loaded")
def _load(http):
    return history.fetch_recent_ids(URL, get=http)


@when(
    parsers.parse('기록 "{ids}" 에 "{spot_id}" 를 한도 {limit:d} 으로 더한다'),
    target_fixture="updated",
)
def _record(ids, spot_id, limit):
    return history.record(_ids(ids), spot_id, limit)


@then(parsers.parse('읽은 기록은 "{ids}" 이다'))
def _loaded_is(loaded, ids):
    assert loaded == _ids(ids)


@then("읽은 기록은 비어 있다")
def _loaded_empty(loaded):
    assert loaded == []


@then("요청은 설정한 주소로 갔고 캐시를 피하는 값이 붙어 있다")
def _request(http):
    args, kwargs = http.calls[0]
    assert args == (URL,)
    assert "t" in kwargs["params"]
    assert kwargs["headers"]["Cache-Control"] == "no-cache"


@then(parsers.parse('새 기록은 "{ids}" 이다'))
def _updated_is(updated, ids):
    assert updated == _ids(ids)
