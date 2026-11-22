"""Moon phase for a moment in time, from the mean synodic month (accurate to about a day)."""

from datetime import UTC, datetime

SYNODIC_MONTH_DAYS = 29.530588853
# A well-known new moon (2000-01-06 18:14 UTC) used as the phase origin.
_REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=UTC)
_SECONDS_PER_DAY = 86400

# Ordered from the new moon onwards; each phase covers 1/8 of the cycle, centred on its moment.
PHASES = (
    "new",
    "waxing_crescent",
    "first_quarter",
    "waxing_gibbous",
    "full",
    "waning_gibbous",
    "last_quarter",
    "waning_crescent",
)


def phase_of(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("moment must be timezone-aware")
    days = (moment - _REFERENCE_NEW_MOON).total_seconds() / _SECONDS_PER_DAY
    fraction = (days / SYNODIC_MONTH_DAYS) % 1
    return PHASES[int(fraction * len(PHASES) + 0.5) % len(PHASES)]
