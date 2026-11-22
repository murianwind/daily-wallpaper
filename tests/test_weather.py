from datetime import datetime

import requests
from pytest_bdd import given, parsers, scenarios, then, when

from support import FakeResponse, Recorder
from wallpaper import config, weather

scenarios("features/weather.feature")

_TODAY = "20261123"


def _ics(date: str, description: str) -> str:
    return (
        "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nSUMMARY:🌧️ 1°C/11°C\r\n"
        f"UID:{date}@short_summary\r\nDESCRIPTION:{description}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    )


def _hourly(entries: str) -> str:
    """'06시 흐림, 10시 비' -> the calendar's description, with literal backslash-n separators."""
    lines = []
    for item in entries.split(", "):
        hour, label = item.split("시 ")
        lines.append(f"[{int(hour):02d}시] ☁️ {label} 5°C (💧80% 🚩2.2m/s)")
    return "\\n".join(lines)


def _serving(text: str) -> Recorder:
    return Recorder(lambda n, *a, **k: FakeResponse(200, text=text))


@when(parsers.parse('날씨 표기 "{label}" 를 분류한다'), target_fixture="condition")
def _classify(label):
    return weather.classify(label)


@then(parsers.parse('분류 결과는 "{expected}" 이다'))
def _classified(condition, expected):
    assert condition == expected


@given(
    parsers.parse("오늘(2026-11-23) 시간별 예보가 {entries} 이다"),
    target_fixture="http",
)
def _forecast(entries):
    return _serving(_ics(_TODAY, _hourly(entries)))


@given("오늘(2026-11-23) 일정의 설명이 접힌 줄로 나뉘어 있다", target_fixture="http")
def _folded():
    text = _ics(_TODAY, _hourly("06시 흐림, 10시 비"))
    folded = text.replace("[10시]", "[10\r\n 시]").replace("DESCRIPTION:", "DESCRIPTION:\r\n ")
    return _serving(folded)


@given("ics 에 다른 날짜의 일정만 있다", target_fixture="http")
def _other_day():
    return _serving(_ics("20261124", _hourly("10시 비")))


@given("ics 요청이 연결 오류로 실패한다", target_fixture="http")
def _connection_error():
    def responder(n, *args, **kwargs):
        raise requests.ConnectionError("down")

    return Recorder(responder)


@given("ics 가 HTTP 500 을 돌려준다", target_fixture="http")
def _server_error():
    return Recorder(lambda n, *a, **k: FakeResponse(500))


@given("ics 가 예상과 다른 내용을 돌려준다", target_fixture="http")
def _unexpected():
    return _serving("<html>not a calendar</html>")


@when(parsers.parse("{hour:d}시에 날씨를 조회한다"), target_fixture="fetched")
def _fetch(http, hour):
    now = datetime(2026, 11, 23, hour, 30, tzinfo=config.KST)
    return weather.fetch_condition(now, get=http)


@then(parsers.parse('조회한 날씨는 "{expected}" 이다'))
def _fetched_is(fetched, expected):
    assert fetched == expected


@then("요청 주소는 설정의 weather.ics 주소이다")
def _request_url(http):
    assert http.calls[0][0][0] == config.WEATHER_ICS_URL
