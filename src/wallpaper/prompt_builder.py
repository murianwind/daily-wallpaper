"""Assemble the image prompt: fixed Jeong Seon style + spot + season + weather + time of day."""

from datetime import date

from .spot_selector import Spot

STYLE = (
    "Korean Joseon-era true-view landscape ink painting (jingyeong sansuhwa) in the manner of "
    "Jeong Seon, strictly monochrome black ink wash in shades of grey, no color, "
    "bold dry-brush strokes, dense vertical texture strokes on granite cliffs, "
    "layered ink wash, aged hanji paper texture in dark charcoal grey, "
    "overall dark low-key tonality, mostly deep charcoal and black with only small light accents, "
    "vertical "
    "hanging-scroll composition, distant panoramic view seen from far away, "
    "a wide vista where the whole landscape appears small in a vast open space, "
    "calm empty sky above the mountains, "
    "painting fills the whole canvas edge to edge, no frame, no paper margin, "
    "no text, no seals, no signature, no border."
)

_SEASON_PHRASES = {
    "spring": "spring, soft pale washes for new leaves and a few blossoming cherry trees",
    "summer": "summer, lush dense foliage in dark ink washes",
    "autumn": "autumn, thinning foliage in soft mid-grey washes",
    "winter": "winter, bare branches and snow dusting the rocks",
}

_TIME_PHRASES = {
    "day": "daytime with soft light, dark charcoal ink washes, heavy low-key tones, rich black ink",
    "night": "night scene, deep black ink wash, very dark low-key tones",
}

# The sun and moon are never drawn by the model: the moon is painted afterwards in its real phase.
_SKY_PHRASES = {
    "day": "Sky: plain empty sky, no sun and no moon are drawn.",
    "night": "Sky: plain dark empty sky, no sun and no moon are drawn.",
}

# Keyed by weather condition (every value weather.classify can return), then by slot.
_WEATHER_PHRASES = {
    "clear": {
        "day": "clear sky, crisp light on the rocks",
        "night": "clear night sky, a few faint stars",
    },
    "partly_cloudy": {
        "day": "scattered clouds drifting among the peaks",
        "night": "thin clouds drifting across the night sky",
    },
    "overcast": {
        "day": "heavy grey clouds, soft diffused light",
        "night": "thick clouds covering the night sky, very dark",
    },
    "fog": {
        "day": "thick mist filling the valleys, peaks half hidden",
        "night": "dense night mist, peaks barely visible",
    },
    "rain": {
        "day": "falling rain, wet dark rocks, low clouds on the peaks",
        "night": "rainy night, dark wet rocks, low clouds",
    },
    "snow": {
        "day": "snow falling softly, pale snow dusting dark rocks and pines",
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
        f"Weather: {weather_phrase}. Time: {time_phrase}. "
        f"{_SKY_PHRASES[slot]}"
    )


def _lookup(table: dict, key: str, label: str):
    try:
        return table[key]
    except KeyError:
        raise ValueError(f"unknown {label}: {key!r}") from None
