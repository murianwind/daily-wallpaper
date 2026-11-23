import dataclasses
import json
import random
from datetime import date, datetime

from PIL import Image, ImageStat
from pytest_bdd import given, parsers, scenarios, then, when

from support import Recorder, capture, png_bytes
from wallpaper import cf_client, config, main, spot_selector
from wallpaper.config import SLOTS

scenarios("features/main.feature")

REQUIRED_ENV = {"CF_ACCOUNT_ID": "account", "CF_API_TOKEN": "token"}
WEBHOOK = "https://discord.test/hook"
LATEST_URL = "https://pages.test/latest.json"


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
    ctx["deployed"] = []  # what the previous deployment's latest.json says was used recently
    ctx["fetch_recent"] = Recorder(lambda n, *a, **k: list(ctx["deployed"]))
    ctx["rng"] = random.Random(0)


def _run(ctx, slot, day):
    return main.run(
        ctx["settings"],
        _now(day),
        slot,
        fetch_condition=ctx["fetch"],
        fetch_recent=ctx["fetch_recent"],
        generate=ctx["generate"],
        notify=ctx["notify"],
        rng=ctx["rng"],
    )


def _written(ctx):
    return json.loads((ctx["settings"].out_dir / "latest.json").read_text(encoding="utf-8"))


def _spots(ctx):
    return spot_selector.load_spots(ctx["settings"].spots_path)


def _spot_in_prompt(ctx):
    """The spot whose visual description went into the prompt sent to the generator."""
    prompt = ctx["generate"].calls[0][0][0]
    matches = [spot for spot in _spots(ctx) if spot.visual in prompt]
    assert len(matches) == 1
    return matches[0]


def _use_deployed_history(ctx, ids):
    ctx["settings"] = dataclasses.replace(ctx["settings"], latest_json_url=LATEST_URL)
    ctx["deployed"] = ids


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


@when("웹훅과 기록 주소 값이 빈 문자열인 환경변수로 설정을 불러온다")
def _load_empty_webhook(ctx, tmp_path, real_spots_path):
    env = {
        **REQUIRED_ENV,
        "DISCORD_WEBHOOK_URL": "",
        "WALLPAPER_MODEL": "",
        "LATEST_JSON_URL": "",
    }
    ctx["loaded"] = main.load_settings(env, real_spots_path, tmp_path)


@when("모델과 웹훅과 기록 주소를 지정한 환경변수로 설정을 불러온다")
def _load_custom(ctx, tmp_path, real_spots_path):
    env = {
        **REQUIRED_ENV,
        "WALLPAPER_MODEL": "@cf/other/model",
        "DISCORD_WEBHOOK_URL": WEBHOOK,
        "LATEST_JSON_URL": LATEST_URL,
    }
    ctx["loaded"] = main.load_settings(env, real_spots_path, tmp_path)


@then(parsers.parse('설정 오류가 발생하고 메시지에 "{first}"와 "{second}"이 들어 있다'))
@then(parsers.parse('설정 오류가 발생하고 메시지에 "{first}"와 "{second}"가 들어 있다'))
def _config_error_mentions(ctx, first, second):
    assert isinstance(ctx["error"], main.ConfigError)
    assert first in str(ctx["error"]) and second in str(ctx["error"])


@then("모델은 기본 모델이고 웹훅과 기록 주소는 없다")
def _defaults(ctx):
    assert ctx["loaded"].model == config.DEFAULT_MODEL
    assert ctx["loaded"].webhook_url is None
    assert ctx["loaded"].latest_json_url is None


@then("설정에 지정한 모델과 웹훅과 기록 주소가 들어 있다")
def _custom(ctx):
    assert ctx["loaded"].model == "@cf/other/model"
    assert ctx["loaded"].webhook_url == WEBHOOK
    assert ctx["loaded"].latest_json_url == LATEST_URL


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


@given("기록 주소가 설정되어 있고 배포된 기록을 따라간다")
def _follow_deployed(ctx):
    _use_deployed_history(ctx, [])


@given("기록 주소가 설정되어 있고 배포된 기록이 목록의 앞쪽 20곳이다")
def _deployed_first_twenty(ctx):
    _use_deployed_history(ctx, [spot.id for spot in _spots(ctx)[:20]])


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


@when(parsers.parse("낮과 밤을 번갈아 {times:d}번 연달아 실행한다"))
def _run_alternating(ctx, times):
    ctx["spot_ids"] = []
    for index in range(times):
        assert _run(ctx, SLOTS[index % len(SLOTS)], "2026-11-19") == 0
        written = _written(ctx)
        ctx["spot_ids"].append(written["spot_id"])
        ctx["deployed"] = written["recent_spot_ids"]  # the deploy step publishes latest.json


@when(parsers.parse("{slot} 시간대로 {day} 에 {times:d}번 연달아 실행한다"))
def _run_repeatedly(ctx, slot, day, times):
    for _ in range(times):
        assert _run(ctx, slot, day) == 0


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
    written = _written(ctx)
    assert written["slot"] == slot
    assert written["weather"] == weather
    assert written["season"] == season
    spot = _spot_in_prompt(ctx)
    assert written["spot_id"] == spot.id
    assert written["spot_area"] == spot.area


@then("알림은 가지 않았다")
def _no_notification(ctx):
    assert ctx["notify"].calls == []


@then("생성기에 보낸 프롬프트에 고른 명승지 묘사가 들어 있다")
def _prompt_has_spot(ctx):
    assert _written(ctx)["spot_id"] == _spot_in_prompt(ctx).id


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


@then(parsers.parse("{times:d}번의 명승지가 모두 다르다"))
def _all_different_spots(ctx, times):
    assert len(ctx["spot_ids"]) == times
    assert len(set(ctx["spot_ids"])) == times


@then("고른 명승지는 배포된 기록에 없다")
def _not_in_deployed(ctx):
    assert _written(ctx)["spot_id"] not in ctx["deployed"]


@then("latest.json 의 기록은 고른 명승지가 맨 앞이고 이전 기록 19곳이 이어진다")
def _history_updated(ctx):
    written = _written(ctx)
    assert written["recent_spot_ids"] == [written["spot_id"], *ctx["deployed"][:19]]


@then("기록은 읽지 않았다")
def _history_not_read(ctx):
    assert ctx["fetch_recent"].calls == []


@then("latest.json 의 기록은 고른 명승지 하나뿐이다")
def _history_single(ctx):
    written = _written(ctx)
    assert written["recent_spot_ids"] == [written["spot_id"]]


@then("두 번의 생성 시드가 서로 다르고 latest.json 에 마지막 시드가 기록된다")
def _seeds_differ(ctx):
    seeds = [call[1]["seed"] for call in ctx["generate"].calls]
    assert len(seeds) == 2 and seeds[0] != seeds[1]
    assert _written(ctx)["seed"] == seeds[-1]


@then("latest.jpg 는 이전 내용 그대로다")
def _previous_kept(ctx):
    assert (ctx["settings"].out_dir / "latest.jpg").read_bytes() == b"OLD IMAGE"


@then("디스코드 알림이 1번 갔고 메시지에 고른 명승지 이름이 들어 있다")
def _notified(ctx):
    assert len(ctx["notify"].calls) == 1
    args = ctx["notify"].calls[0][0]
    assert args[0] == WEBHOOK
    assert _spot_in_prompt(ctx).name_ko in args[1]


@then(parsers.parse('latest.json 의 달 모양은 "{phase}" 이다'))
def _moon_recorded(ctx, phase):
    assert _written(ctx)["moon_phase"] == phase


@then("latest.json 의 해달 위치는 왼쪽이거나 오른쪽이다")
def _side_recorded(ctx):
    assert _written(ctx)["sky_side"] in config.SKY_SIDES


@when(parsers.parse("{slot} 시간대로 {day} 에 {times:d}번 연달아 실행하며 달 위치를 모은다"))
def _run_collecting_sides(ctx, slot, day, times):
    ctx["sides"] = set()
    for _ in range(times):
        assert _run(ctx, slot, day) == 0
        ctx["sides"].add(_written(ctx)["sky_side"])


@then("모은 달 위치에 왼쪽과 오른쪽이 모두 있다")
def _both_sides(ctx):
    assert ctx["sides"] == set(config.SKY_SIDES)


def _moon_spot_level(ctx):
    side = _written(ctx)["sky_side"]
    with Image.open(ctx["settings"].out_dir / "latest.jpg") as image:
        gray = image.convert("L")
        return gray.getpixel(
            (
                round(gray.width * config.MOON_CENTER_X_RATIOS[side]),
                round(gray.height * config.MOON_CENTER_Y_RATIO),
            )
        )


@then("latest.jpg 의 달 자리는 밝다")
def _moon_drawn(ctx):
    assert _moon_spot_level(ctx) > 200


@then("latest.jpg 의 달 자리는 밝지 않다")
def _moon_not_drawn(ctx):
    assert _moon_spot_level(ctx) < 150


@given("폭포 명승지만 있는 명승지 파일을 쓴다")
def _only_waterfalls(ctx, tmp_path):
    items = [
        {
            "id": f"falls-{index}",
            "name_ko": f"폭포{index}",
            "area": "x",
            "visual": "v",
            "waterfall": True,
        }
        for index in (1, 2)
    ]
    path = tmp_path / "waterfalls.json"
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    ctx["settings"] = dataclasses.replace(ctx["settings"], spots_path=path)


@then("생성기에 보낸 프롬프트의 물줄기는 달의 반대쪽 3분의 1 에 있다")
def _stream_opposite_moon(ctx):
    moon_side = _written(ctx)["sky_side"]
    stream_side = next(side for side in config.SKY_SIDES if side != moon_side)
    assert f"in the {stream_side} third of the frame" in ctx["generate"].calls[0][0][0]


def _bright_dot_ratio(ctx):
    with Image.open(ctx["settings"].out_dir / "latest.jpg") as image:
        gray = image.convert("L")
        median = ImageStat.Stat(gray).median[0]
        mask = gray.point(lambda value: 255 if value >= median + 25 else 0)
        return ImageStat.Stat(mask).mean[0] / 255


@then("latest.jpg 의 밝은 점은 많다")
def _precipitation_drawn(ctx):
    assert _bright_dot_ratio(ctx) > 0.002


@then("latest.jpg 의 밝은 점은 없다")
def _no_precipitation(ctx):
    assert _bright_dot_ratio(ctx) < 0.0005
