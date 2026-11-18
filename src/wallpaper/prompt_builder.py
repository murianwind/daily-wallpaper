"""Assemble the image prompt: fixed Jeong Seon style + spot + season + weather + time of day."""

from datetime import date

from .spot_selector import Spot

STYLE = (
    "Korean Joseon-era true-view landscape ink painting (jingyeong sansuhwa) in the manner of "
    "Jeong Seon, bold dry-brush strokes, dense vertical texture strokes on granite cliffs, "
    "layered ink wash with restrained pale colors, aged hanji paper texture, vertical "
    "hanging-scroll composition, calm empty sky in the upper third, "
    "no text, no seals, no signature, no border."
)

_SEASON_PHRASES = {
    "spring": "spring, fresh pale green leaves and a few blossoming mountain cherry trees",
    "summer": "summer, lush deep green foliage",
    "autumn": "autumn, foliage in muted ochre and russet",
    "winter": "winter, bare branches and snow dusting the rocks",
}

_TIME_PHRASES = {
    "day": "bright daytime, luminous pale washes, light paper tone, high-key",
    "night": (
        "night scene, deep indigo and black ink wash, dark low-key tones, a faint pale moon glow"
    ),
}

# Keyed by weather condition (every value weather.classify can return), then by slot.
_WEATHER_PHRASES = {
    "clear": {
        "day": "clear sky, crisp sunlight on the rocks",
        "night": "clear night sky, a bright moon, a few faint stars",
    },
    "partly_cloudy": {
        "day": "scattered clouds drifting among the peaks",
        "night": "moon half-veiled by drifting clouds",
    },
    "overcast": {
        "day": "heavy grey clouds, soft diffused light",
        "night": "thick clouds hiding the moon, very dark",
    },
    "fog": {
        "day": "thick mist filling the valleys, peaks half hidden",
        "night": "dense moonlit mist, peaks barely visible",
    },
    "rain": {
        "day": "falling rain, wet dark rocks, low clouds on the peaks",
        "night": "rainy night, dark wet rocks, moon hidden",
    },
    "snow": {
        "day": "snow falling softly, white rocks and pines",
        "night": "snowfall at night, pale snow glowing in the dark",
    },
    "thunderstorm": {
        "day": "stormy dark sky with sheets of rain",
        "night": "stormy night, heavy dark clouds and rain",
    },
    "unknown": {
        "day": "calm quiet atmosphere",
        "night": "calm quiet night atmosphere",
    },
}


def season_of(day: date) -> str:
    if day.month in (3, 4, 5):
        return "spring"
    if day.month in (6, 7, 8):
        return "summer"
    if day.month in (9, 10, 11):
        return "autumn"
    return "winter"


def build_prompt(spot: Spot, slot: str, season: str, condition: str) -> str:
    time_phrase = _lookup(_TIME_PHRASES, slot, "slot")
    season_phrase = _lookup(_SEASON_PHRASES, season, "season")
    weather_phrase = _lookup(
        _lookup(_WEATHER_PHRASES, condition, "weather condition"), slot, "slot"
    )
    return (
        f"{STYLE} Scene: {spot.visual}. Season: {season_phrase}. "
        f"Weather: {weather_phrase}. Time: {time_phrase}."
    )


def _lookup(table: dict, key: str, label: str):
    try:
        return table[key]
    except KeyError:
        raise ValueError(f"unknown {label}: {key!r}") from None
