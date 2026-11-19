import yaml
from pytest_bdd import given, parsers, scenarios, then

from conftest import ROOT

scenarios("features/workflow.feature")

WORKFLOW_PATH = ROOT / ".github" / "workflows" / "wallpaper.yml"


@given("워크플로 파일", target_fixture="workflow")
def _workflow():
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _schedules(workflow):
    # PyYAML reads the bare key `on` as boolean True.
    return workflow[True]["schedule"]


@then(parsers.parse("예약 실행은 {count:d}건이다"))
def _schedule_count(workflow, count):
    assert len(_schedules(workflow)) == count


@then(parsers.parse('모든 예약 실행의 시간대는 "{zone}" 이다'))
def _timezone(workflow, zone):
    assert all(entry.get("timezone") == zone for entry in _schedules(workflow))


@then(parsers.parse('예약 실행 시각은 "{first}" 와 "{second}" 이다'))
def _cron_times(workflow, first, second):
    assert sorted(entry["cron"] for entry in _schedules(workflow)) == sorted([first, second])


@then(parsers.parse('예약 실행의 시간대 입력값은 "{expected}" 이다'))
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
