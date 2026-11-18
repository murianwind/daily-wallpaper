import base64

import requests
from pytest_bdd import given, parsers, scenarios, then, when

from support import FakeResponse, Recorder, capture, png_bytes
from wallpaper import cf_client

scenarios("features/generation.feature")

ACCOUNT_ID = "ACCOUNT123"
API_TOKEN = "TOKEN456"
MODEL = "@cf/test/model"
IMAGE = png_bytes(8, 8)
OK_BODY = {"result": {"image": base64.b64encode(IMAGE).decode()}, "success": True}


def _flaky(failures, failure):
    """Responder that fails `failures` times (via failure(n)) and then succeeds."""

    def responder(number, *args, **kwargs):
        if number <= failures:
            return failure(number)
        return FakeResponse(200, OK_BODY)

    return responder


def _status(code):
    return lambda number: FakeResponse(code, text="error")


def _drop(number):
    raise requests.ConnectionError("connection dropped")


@given("Cloudflare가 정상 응답한다", target_fixture="post")
def _ok():
    return Recorder(lambda n, *a, **k: FakeResponse(200, OK_BODY))


@given(
    parsers.parse("Cloudflare가 처음 {failures:d}번은 HTTP {code:d} 을 돌려주고 그다음에 성공한다"),
    target_fixture="post",
)
def _fail_then_ok(failures, code):
    return Recorder(_flaky(failures, _status(code)))


@given(
    parsers.parse("Cloudflare 연결이 처음 {failures:d}번은 끊기고 그다음에 성공한다"),
    target_fixture="post",
)
def _drop_then_ok(failures):
    return Recorder(_flaky(failures, _drop))


@given(parsers.parse("Cloudflare가 항상 HTTP {code:d} 을 돌려준다"), target_fixture="post")
def _always(code):
    return Recorder(lambda n, *a, **k: FakeResponse(code, text="error"))


@given("Cloudflare가 200 이지만 이미지가 없는 응답을 준다", target_fixture="post")
def _no_image():
    return Recorder(lambda n, *a, **k: FakeResponse(200, {"result": {}, "success": True}))


@given("Cloudflare 연결 오류 메시지에 요청 주소와 토큰이 들어 있다", target_fixture="post")
def _leaky_error():
    def responder(number, url, **kwargs):
        raise requests.ConnectionError(f"failed to reach {url} with {kwargs['headers']}")

    return Recorder(responder)


@when("프롬프트로 이미지를 생성한다")
def _generate(post, ctx):
    ctx["sleeps"] = []
    ctx["result"], ctx["error"] = capture(
        cf_client.generate_image,
        "a prompt",
        account_id=ACCOUNT_ID,
        api_token=API_TOKEN,
        model=MODEL,
        width=880,
        height=1920,
        seed=100,
        post=post,
        sleep=ctx["sleeps"].append,
    )


@then("이미지 바이트를 받는다")
def _got_image(ctx):
    assert ctx["error"] is None
    assert ctx["result"] == IMAGE


@then(parsers.parse("요청은 {count:d}번 보냈다"))
def _request_count(post, count):
    assert len(post.calls) == count


@then(parsers.parse("재시도 사이에 {count:d}번 대기했다"))
def _sleep_count(ctx, count):
    assert len(ctx["sleeps"]) == count


@then("요청 주소에 계정 ID와 모델이 들어 있다")
def _url(post):
    url = post.calls[0][0][0]
    assert url == f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL}"


@then("요청 폼에 prompt, width, height, seed 가 들어 있다")
def _form(post):
    form = post.calls[0][1]["files"]
    assert form == {
        "prompt": (None, "a prompt"),
        "width": (None, "880"),
        "height": (None, "1920"),
        "seed": (None, "100"),
    }


@then("인증 헤더에 토큰이 들어 있다")
def _auth(post):
    assert post.calls[0][1]["headers"]["Authorization"] == f"Bearer {API_TOKEN}"


@then("생성 오류가 발생한다")
def _generation_error(ctx):
    assert isinstance(ctx["error"], cf_client.GenerationError)


@then("시도마다 seed 가 서로 다르고 첫 seed 는 100 이다")
def _seeds(post):
    seeds = [int(call[1]["files"]["seed"][1]) for call in post.calls]
    assert seeds[0] == 100
    assert len(set(seeds)) == len(seeds)


@then("오류 메시지에 계정 ID와 토큰이 없다")
def _no_secrets(ctx):
    message = str(ctx["error"])
    assert ACCOUNT_ID not in message
    assert API_TOKEN not in message
