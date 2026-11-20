import yaml
from pytest_bdd import given, parsers, scenarios, then

from conftest import ROOT

scenarios("features/workflow.feature")

WORKFLOW_PATH = ROOT / ".github" / "workflows" / "wallpaper.yml"


@given("워크플로 파일", target_fixture="workflow")
def _workflow():
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _triggers(workflow):
    # PyYAML reads the bare key `on` as boolean True.
    return workflow[True]


@then(parsers.parse('외부 호출 이벤트는 "{event}" 하나다'))
def _dispatch_event(workflow, event):
    assert _triggers(workflow)["repository_dispatch"]["types"] == [event]


@then("수동 실행도 가능하다")
def _manual_run(workflow):
    assert "workflow_dispatch" in _triggers(workflow)


@then("예약 실행은 없다")
def _no_schedule(workflow):
    assert "schedule" not in _triggers(workflow)


@then("예약 실행을 살리기 위한 keepalive 작업도 없다")
def _no_keepalive(workflow):
    assert "keepalive" not in workflow["jobs"]


@then(parsers.parse('생성 단계의 시간대 입력값은 "{expected}" 이다'))
def _slot_input(workflow, expected):
    steps = workflow["jobs"]["generate"]["steps"]
    slot = next(step["env"]["SLOT"] for step in steps if "env" in step and "SLOT" in step["env"])
    assert slot == f"${{{{ inputs.slot || '{expected}' }}}}"


@then("생성 단계의 LATEST_JSON_URL 은 이 저장소의 Pages 주소 latest.json 이다")
def _latest_url(workflow):
    steps = workflow["jobs"]["generate"]["steps"]
    url = next(
        step["env"]["LATEST_JSON_URL"] for step in steps if "LATEST_JSON_URL" in step.get("env", {})
    )
    assert url == (
        "https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}"
        "/latest.json"
    )
