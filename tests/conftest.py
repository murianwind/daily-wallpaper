from pathlib import Path

import pytest
from pytest_bdd import given

from wallpaper import spot_selector

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ctx():
    """Per-scenario scratch space shared between steps."""
    return {}


@pytest.fixture
def real_spots_path():
    return ROOT / "data" / "spots.json"


@given("실제 명승지 데이터 파일", target_fixture="spots")
def _real_spots(real_spots_path):
    return spot_selector.load_spots(real_spots_path)
