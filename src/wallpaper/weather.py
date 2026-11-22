"""Current Seoul weather read from the weather-calendar .ics, reduced to a few prompt conditions."""

import logging
import re
from datetime import datetime

import requests

from wallpaper.config import WEATHER_ICS_URL

logger = logging.getLogger(__name__)

UNKNOWN = "unknown"

# First match wins, so "비/눈" (rain and snow mixed) is read as snow.
_LABEL_CONDITIONS = (
    ("뇌우", "thunderstorm"),
    ("눈", "snow"),
    ("비", "rain"),
    ("소나기", "rain"),
    ("안개", "fog"),
    ("구름많음", "partly_cloudy"),
    ("흐림", "overcast"),
    ("맑음", "clear"),
)

# One line of the hourly description: "[10시] 🌧️ 비 5°C (...)" -> hour and label.
_HOURLY_ENTRY = re.compile(r"\[(\d{2})시\]\s+\S+\s+(\S+)\s+-?\d+°C")
_FOLDED_LINE = re.compile(r"\r?\n[ \t]")


def classify(label: str) -> str:
    for keyword, condition in _LABEL_CONDITIONS:
        if keyword in label:
            return condition
    return UNKNOWN


def fetch_condition(now: datetime, get=requests.get, timeout: int = 10) -> str:
    """Condition at `now` (KST) from today's hourly forecast; any failure degrades to UNKNOWN."""
    try:
        response = get(WEATHER_ICS_URL, timeout=timeout)
        response.raise_for_status()
        return classify(_label_at(_today_description(response.text, now), now.hour))
    except (requests.RequestException, ValueError) as exc:
        logger.warning("weather lookup failed (%s); continuing without weather", type(exc).__name__)
        return UNKNOWN


def _today_description(ics_text: str, now: datetime) -> str:
    unfolded = _FOLDED_LINE.sub("", ics_text)
    uid = f"UID:{now:%Y%m%d}@short_summary"
    for event in unfolded.split("BEGIN:VEVENT")[1:]:
        if uid in event:
            return event.split("DESCRIPTION:", 1)[1]
    raise ValueError("no event for today")


def _label_at(description: str, hour: int) -> str:
    """The label of the forecast hour closest to `hour`."""
    entries = [(int(found[0]), found[1]) for found in _HOURLY_ENTRY.findall(description)]
    if not entries:
        raise ValueError("no hourly entries")
    return min(entries, key=lambda entry: abs(entry[0] - hour))[1]
