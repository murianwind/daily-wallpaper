import dataclasses
import json
from datetime import date, datetime

from PIL import Image
from pytest_bdd import given, parsers, scenarios, then, when

from support import Recorder, capture, png_bytes
from wallpaper import cf_client, config, main, spot_selector

scenarios("features/main.feature")

REQUIRED_ENV = {"CF_ACCOUNT_ID": "account", "CF_API_TOKEN": "token"}
WEBHOOK = "https://discord.test/hook"


def _now(day="2026-11-19", hour=6, minute=0):
    parsed = date.fromisoformat(day)
    return datetime(parsed.year, parsed.month, parsed.day, hour, minute, tzinfo=config.KST)


def _settings(tmp_path, real_spots_path):
    env = {**REQUIRED_ENV, "WALLPAPER_MODEL": "@cf/test/model"}
    return main.load_settings(env, real_spots_path, tmp_path / "site")


def _prepare(ctx, tmp_path, real_spots_path, generate):
    ctx["settings"] = _settings(tmp_path, real_spots_path)
    ctx["generate"] = Recorder(generate)
    ctx["notify"] = Recorder(lambda n, *a, **k: True)
    ctx["fetch"] = Recorder(lambda n, *a, **k: "clear")


def _run(ctx, slot, day):
    return main.run(
        ctx["settings"],
        _now(day),
        slot,
        fetch_condition=ctx["fetch"],
        generate=ctx["generate"],
        notify=ctx["notify"],
    )


def _todays_spot(ctx, slot="day", day="2026-11-19"):
    spots = spot_selector.load_spots(ctx["settings"].spots_path)
    return spot_selector.select_spot(spots, date.fromisoformat(day), slot)


# ---- slot resolution -------------------------------------------------------------------


@when(
    parsers.parse('요청 "{requested}" 와 한국 시각 {hour:d}시 {minute:d}분 으로 시간대를 정한다'),
    target_fixture="resolved",
)
def _resolve(requested, hour, minute):
    return main.resolve_slot(requested, _now(hour=hour, minute=minute))


@when(
    parsers.parse(
        '요청 "{requested}" 와 한국 시각 {hour:d}시 {minute:d}분 으로 시간대를 정하려 한다'
    )
)
def _try_resolve(ctx, requested, hour, minute):
    _, ctx["error"] = capture(main.resolve_slot, requested, _now(hour=hour, minute=minute))


@then(parsers.parse('정해진 시간대는 "{expected}" 이다'))
def _resolved_is(resolved, expected):
    assert resolved == expected


@then("설정 오류가 발생한다")
def _config_error(ctx):
    assert isinstance(ctx["error"], main.ConfigError)


# ---- settings ------------------------------------------------------------------------------


@when("환경변수 없이 설정을 불러오려 한다")
def _load_without_env(ctx, tmp_path, real_spots_path):
    _, ctx["error"] = capture(main.load_settings, {}, real_spots_path, tmp_path)


@when("필수 환경변수만으로 설정을 불러온다")
def _load_required(ctx, tmp_path, real_spots_path):
    ctx["loaded"] = main.load_settings(dict(REQUIRED_ENV), real_spots_path, tmp_path)


@when("웹훅 값이 빈 문자열인 환경변수로 설정을 불러온다")
def _load_empty_webhook(ctx, tmp_path, real_spots_path):
    env = {**REQUIRED_ENV, "DISCORD_WEBHOOK_URL": "", "WALLPAPER_MODEL": ""}
    ctx["loaded"] = main.load_settings(env, real_spots_path, tmp_path)


@when("모델과 웹훅을 지정한 환경변수로 설정을 불러온다")
def _load_custom(ctx, tmp_path, real_spots_path):
    env = {**REQUIRED_ENV, "WALLPAPER_MODEL": "@cf/other/model", "DISCORD_WEBHOOK_URL": WEBHOOK}
    ctx["loaded"] = main.load_settings(env, real_spots_path, tmp_path)


@then(parsers.parse('설정 오류가 발생하고 메시지에 "{first}"와 "{second}"이 들어 있다'))
@then(parsers.parse('설정 오류가 발생하고 메시지에 "{first}"와 "{second}"가 들어 있다'))
def _config_error_mentions(ctx, first, second):
    assert isinstance(ctx["error"], main.ConfigError)
    assert first in str(ctx["error"]) and second in str(ctx["error"])


@then("모델은 기본 모델이고 웹훅은 없다")
def _defaults(ctx):
    assert ctx["loaded"].model == config.DEFAULT_MODEL
    assert ctx["loaded"].webhook_url is None


@then("설정에 지정한 모델과 웹훅이 들어 있다")
def _custom(ctx):
    assert ctx["loaded"].model == "@cf/other/model"
    assert ctx["loaded"].webhook_url == WEBHOOK


# ---- run ---------------------------------------------------------------------------------------


@given("정상 설정과 정상 동작하는 생성기")
def _healthy(ctx, tmp_path, real_spots_path):
    _prepare(ctx, tmp_path, real_spots_path, lambda n, *a, **k: png_bytes(880, 1920))


@given("정상 설정과 항상 실패하는 생성기")
def _failing(ctx, tmp_path, real_spots_path):
    def responder(number, *args, **kwargs):
        raise cf_client.GenerationError("boom")

    _prepare(ctx, tmp_path, real_spots_path, responder)


@given("정상 설정과 이미지가 아닌 데이터를 주는 생성기")
def _garbage(ctx, tmp_path, real_spots_path):
    _prepare(ctx, tmp_path, real_spots_path, lambda n, *a, **k: b"not an image")


@given(parsers.parse('날씨가 "{condition}" 으로 조회된다'))
def _weather_is(ctx, condition):
    ctx["fetch"] = Recorder(lambda n, *a, **k: condition)


@given("디스코드 웹훅이 설정되어 있다")
def _webhook(ctx):
    ctx["settings"] = dataclasses.replace(ctx["settings"], webhook_url=WEBHOOK)


@given("이전에 만든 latest.jpg 가 있다")
def _previous(ctx):
    out_dir = ctx["settings"].out_dir
    out_dir.mkdir(parents=True)
    (out_dir / "latest.jpg").write_bytes(b"OLD IMAGE")


@when(parsers.parse("{slot} 시간대로 {day} 에 실행한다"))
def _run_once(ctx, slot, day):
    ctx["code"] = _run(ctx, slot, day)


@when(parsers.parse("day 와 night 로 연달아 {day} 에 실행한다"))
def _run_both(ctx, day):
    ctx["spot_ids"] = []
    for slot in ("day", "night"):
        assert _run(ctx, slot, day) == 0
        written = json.loads((ctx["settings"].out_dir / "latest.json").read_text(encoding="utf-8"))
        ctx["spot_ids"].append(written["spot_id"])


@when("환경변수 없이 명령줄로 실행한다")
def _run_cli(ctx, tmp_path):
    ctx["cli_code"] = main.main(["--slot", "day", "--out", str(tmp_path / "site")], env={})


@then(parsers.parse("종료 코드는 {code:d} 이다"))
def _exit_code(ctx, code):
    assert ctx["code"] == code


@then(parsers.parse("명령줄 종료 코드는 {code:d} 이다"))
def _cli_exit_code(ctx, code):
    assert ctx["cli_code"] == code


@then(parsers.parse("out 폴더에 {width:d}x{height:d} 크기의 latest.jpg 가 있다"))
def _jpg_exists(ctx, width, height):
    with Image.open(ctx["settings"].out_dir / "latest.jpg") as image:
        assert image.format == "JPEG"
        assert image.size == (width, height)


@then("out 폴더에 latest.jpg 가 없다")
def _jpg_missing(ctx):
    assert not (ctx["settings"].out_dir / "latest.jpg").exists()


@then(
    parsers.parse(
        'latest.json 에 slot 이 "{slot}" 이고 weather 가 "{weather}" 이고 season 이 "{season}" 이다'
    )
)
def _json_fields(ctx, slot, weather, season):
    written = json.loads((ctx["settings"].out_dir / "latest.json").read_text(encoding="utf-8"))
    assert written["slot"] == slot
    assert written["weather"] == weather
    assert written["season"] == season
    spot = _todays_spot(ctx, slot)
    assert written["spot_id"] == spot.id
    assert written["spot_area"] == spot.area


@then("알림은 가지 않았다")
def _no_notification(ctx):
    assert ctx["notify"].calls == []


@then("생성기에 보낸 프롬프트에 오늘의 명승지 묘사가 들어 있다")
def _prompt_has_spot(ctx):
    prompt = ctx["generate"].calls[0][0][0]
    assert _todays_spot(ctx, "night").visual in prompt


@then(parsers.parse('생성기에 보낸 프롬프트에 "{text}" 가 들어 있다'))
def _prompt_has(ctx, text):
    assert text in ctx["generate"].calls[0][0][0]


@then(parsers.parse('생성기는 모델 "{model}" 과 {width:d}x{height:d} 크기로 호출되었다'))
def _generator_args(ctx, model, width, height):
    kwargs = ctx["generate"].calls[0][1]
    assert kwargs["model"] == model
    assert (kwargs["width"], kwargs["height"]) == (width, height)
    assert kwargs["account_id"] == "account"
    assert kwargs["api_token"] == "token"


@then("두 실행의 명승지가 서로 다르다")
def _different_spots(ctx):
    assert ctx["spot_ids"][0] != ctx["spot_ids"][1]


@then("latest.jpg 는 이전 내용 그대로다")
def _previous_kept(ctx):
    assert (ctx["settings"].out_dir / "latest.jpg").read_bytes() == b"OLD IMAGE"


@then("디스코드 알림이 1번 갔고 메시지에 오늘의 명승지 이름이 들어 있다")
def _notified(ctx):
    assert len(ctx["notify"].calls) == 1
    args = ctx["notify"].calls[0][0]
    assert args[0] == WEBHOOK
    assert _todays_spot(ctx).name_ko in args[1]
