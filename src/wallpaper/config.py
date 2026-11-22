"""Constants shared across modules. Spot data lives in data/spots.json."""

from datetime import timedelta, timezone

KST = timezone(timedelta(hours=9))
SLOTS = ("day", "night")
# Which side of the sky the sun or moon is placed on (never the centre).
SKY_SIDES = ("left", "right")

# Weather reference point: Seoul.
SEOUL_LATITUDE = 37.5665
SEOUL_LONGITUDE = 126.9780

# FLUX.2 [klein] accepts 256-1920 per side. The picture only fills the lower part of the screen
# (see TOP_BLANK_RATIO), so it is generated at that area's aspect ratio (~0.69), not the phone's.
GEN_WIDTH = 1104
GEN_HEIGHT = 1600
# Fraction trimmed from every side of the generated image to drop any paper-edge border the model
# paints despite the prompt (measured: about 3-6% on the sides, so 7% leaves a safety margin).
EDGE_TRIM_RATIO = 0.07
# Fraction of the screen height kept as plain blank background above the picture.
TOP_BLANK_RATIO = 1 / 3
# Fraction of the screen height over which the picture fades into that blank background.
TOP_FADE_RATIO = 0.10
# Brightness of the blank sky at the very top edge, relative to where it meets the picture.
TOP_DIM_RATIO = 0.8
# The blank sky takes the picture's sky tones in this many horizontal zones, blended smoothly.
SKY_TONE_COLUMNS = 8
# iOS picks white text on dark wallpapers, so the picture's mean brightness (0-255) is capped here.
# Measured on the author's iPhone: a wallpaper averaging ~120 kept white text, ~165 turned it dark.
# The blank sky above the picture runs a few points brighter than the picture itself.
MAX_MEAN_BRIGHTNESS = 112
# Darkening lifts black to this level instead of crushing it, so dark ink detail stays readable.
MIN_BLACK_LEVEL = 24
# The moon is painted by us (image models draw moon phases unreliably): just below the blank top
# area, on the left or right, never at the centre. Sizes and positions are fractions of the screen.
MOON_RADIUS_RATIO = 0.045
MOON_CENTER_Y_RATIO = 0.37
MOON_CENTER_X_RATIOS = {"left": 0.25, "right": 0.75}
MOON_LEVEL = 235
# Weather in which the night moon can be seen (anything else hides it behind clouds, rain or fog).
MOON_VISIBLE_CONDITIONS = ("clear", "partly_cloudy", "unknown")
# iPhone 15 Pro screen size in pixels.
WALLPAPER_WIDTH = 1179
WALLPAPER_HEIGHT = 2556

DEFAULT_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
# Total tries per image, kept small so retries stay inside the free daily allowance.
MAX_ATTEMPTS = 3
