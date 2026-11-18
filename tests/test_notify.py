import requests
from pytest_bdd import given, parsers, scenarios, then, when

from support import FakeResponse, Recorder
from wallpaper import notifier

scenarios("features/notify.feature")


@given("정상 동작하는 웹훅", target_fixture="post")
def _ok():
    return Recorder(lambda n, *a, **k: FakeResponse(204))


@given("연결이 끊기는 웹훅", target_fixture="post")
def _dropped():
    def responder(number, *args, **kwargs):
        raise requests.ConnectionError("dropped")

    return Recorder(responder)


@given("HTTP 400 을 돌려주는 웹훅", target_fixture="post")
def _bad_request():
    return Recorder(lambda n, *a, **k: FakeResponse(400))


@when(parsers.parse('웹훅 주소 "{url}" 로 "{message}" 메시지를 보낸다'))
def _send(post, ctx, url, message):
    ctx["sent"] = notifier.notify_failure(url, message, post=post)


@when('웹훅 주소 없이 "생성 실패" 메시지를 보낸다')
def _send_without_url(post, ctx):
    ctx["sent"] = notifier.notify_failure(None, "생성 실패", post=post)


@when(parsers.parse('웹훅 주소 "{url}" 로 5000자짜리 메시지를 보낸다'))
def _send_long(post, ctx, url):
    ctx["sent"] = notifier.notify_failure(url, "가" * 5000, post=post)


@then("알림 결과는 성공이다")
def _success(ctx):
    assert ctx["sent"] is True


@then("알림 결과는 실패이다")
def _failure(ctx):
    assert ctx["sent"] is False


@then(parsers.parse('웹훅으로 "{text}" 내용이 1번 전송되었다'))
def _sent_once(post, text):
    assert len(post.calls) == 1
    assert post.calls[0][1]["json"] == {"content": text}


@then("전송은 한 번도 일어나지 않았다")
def _never_sent(post):
    assert post.calls == []


@then("전송된 내용은 2000자를 넘지 않는다")
def _within_limit(post):
    assert len(post.calls[0][1]["json"]["content"]) <= 2000
