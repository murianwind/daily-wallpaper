"""Constants shared across modules. Spot data lives in data/spots.json."""

from datetime import timedelta, timezone

KST = timezone(timedelta(hours=9))
SLOTS = ("day", "night")

# Weather reference point: Seoul.
SEOUL_LATITUDE = 37.5665
SEOUL_LONGITUDE = 126.9780

# FLUX.2 [klein] accepts 256-1920 per side; 880x1920 is the closest fit to an iPhone's aspect ratio.
GEN_WIDTH = 880
GEN_HEIGHT = 1920
# Fraction trimmed from every side of the generated image to drop any paper-edge border the model
# paints despite the prompt (measured: about 3-6% on the sides, so 7% leaves a safety margin).
EDGE_TRIM_RATIO = 0.07
# iPhone 15 Pro screen size in pixels.
WALLPAPER_WIDTH = 1179
WALLPAPER_HEIGHT = 2556

DEFAULT_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
# Total tries per image, kept small so retries stay inside the free daily allowance.
MAX_ATTEMPTS = 3
