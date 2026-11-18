import requests
from pytest_bdd import given, parsers, scenarios, then, when

from support import FakeResponse, Recorder
from wallpaper import config, weather

scenarios("features/weather.feature")


@when(parsers.parse("날씨 코드 {code:d} 를 분류한다"), target_fixture="condition")
def _classify(code):
    return weather.classify(code)


@when("날씨 코드가 없는 상태를 분류한다", target_fixture="condition")
def _classify_none():
    return weather.classify(None)


@then(parsers.parse('분류 결과는 "{expected}" 이다'))
def _classified(condition, expected):
    assert condition == expected


@given(parsers.parse("Open-Meteo가 날씨 코드 {code:d} 을 돌려준다"), target_fixture="http")
def _ok(code):
    return Recorder(lambda n, *a, **k: FakeResponse(200, {"current": {"weather_code": code}}))


@given("Open-Meteo 요청이 연결 오류로 실패한다", target_fixture="http")
def _connection_error():
    def responder(n, *args, **kwargs):
        raise requests.ConnectionError("down")

    return Recorder(responder)


@given("Open-Meteo가 HTTP 500 을 돌려준다", target_fixture="http")
def _server_error():
    return Recorder(lambda n, *a, **k: FakeResponse(500))


@given("Open-Meteo가 예상과 다른 JSON 을 돌려준다", target_fixture="http")
def _unexpected_json():
    return Recorder(lambda n, *a, **k: FakeResponse(200, {"unexpected": True}))


@when("서울 날씨를 조회한다", target_fixture="fetched")
def _fetch(http):
    return weather.fetch_condition(config.SEOUL_LATITUDE, config.SEOUL_LONGITUDE, get=http)


@then(parsers.parse('조회한 날씨는 "{expected}" 이다'))
def _fetched_is(fetched, expected):
    assert fetched == expected


@then("요청에 서울 좌표와 Asia/Seoul 시간대와 weather_code 항목이 들어 있다")
def _request_params(http):
    params = http.calls[0][1]["params"]
    assert params["latitude"] == config.SEOUL_LATITUDE
    assert params["longitude"] == config.SEOUL_LONGITUDE
    assert params["timezone"] == "Asia/Seoul"
    assert params["current"] == "weather_code"
