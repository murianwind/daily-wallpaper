"""Seoul weather from Open-Meteo, reduced to a handful of conditions for the prompt."""

import logging

import requests

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
UNKNOWN = "unknown"

# WMO weather interpretation codes, as used by Open-Meteo.
_RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}
_SNOW_CODES = {71, 73, 75, 77, 85, 86}
_THUNDERSTORM_CODES = {95, 96, 99}


def classify(code: int | None) -> str:
    if code == 0:
        return "clear"
    if code in (1, 2):
        return "partly_cloudy"
    if code == 3:
        return "overcast"
    if code in (45, 48):
        return "fog"
    if code in _RAIN_CODES:
        return "rain"
    if code in _SNOW_CODES:
        return "snow"
    if code in _THUNDERSTORM_CODES:
        return "thunderstorm"
    return UNKNOWN


def fetch_condition(latitude: float, longitude: float, get=requests.get, timeout: int = 10) -> str:
    """Current condition at the given point; any failure degrades to UNKNOWN instead of raising."""
    try:
        response = get(
            OPEN_METEO_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "weather_code",
                "timezone": "Asia/Seoul",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return classify(response.json()["current"]["weather_code"])
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        logger.warning("weather lookup failed (%s); continuing without weather", type(exc).__name__)
        return UNKNOWN
