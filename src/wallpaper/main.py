"""Entry point: pick a spot, read the weather, generate the image, save it for GitHub Pages."""

import argparse
import json
import logging
import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import (
    cf_client,
    history,
    image_post,
    moon_phase,
    notifier,
    prompt_builder,
    spot_selector,
    weather,
)
from .config import (
    DEFAULT_MODEL,
    GEN_HEIGHT,
    GEN_WIDTH,
    KST,
    MOON_VISIBLE_CONDITIONS,
    SKY_SIDES,
    SLOTS,
    WALLPAPER_HEIGHT,
    WALLPAPER_WIDTH,
)
from .moon_painter import Moon
from .precipitation import precipitation_for

logger = logging.getLogger(__name__)

DEFAULT_SPOTS_PATH = Path(__file__).resolve().parents[2] / "data" / "spots.json"
# Runs before noon (KST) are the daytime wallpaper, later runs the night one.
_NIGHT_STARTS_AT_HOUR = 12
_SEED_LIMIT = 1_000_000_000


class ConfigError(RuntimeError):
    """Missing or invalid configuration."""


@dataclass(frozen=True)
class Settings:
    account_id: str
    api_token: str
    model: str
    webhook_url: str | None
    latest_json_url: str | None
    spots_path: Path
    out_dir: Path


def load_settings(env, spots_path: Path, out_dir: Path) -> Settings:
    missing = [name for name in ("CF_ACCOUNT_ID", "CF_API_TOKEN") if not env.get(name)]
    if missing:
        raise ConfigError(f"missing environment variables: {', '.join(missing)}")
    return Settings(
        account_id=env["CF_ACCOUNT_ID"],
        api_token=env["CF_API_TOKEN"],
        model=env.get("WALLPAPER_MODEL") or DEFAULT_MODEL,
        webhook_url=env.get("DISCORD_WEBHOOK_URL") or None,
        latest_json_url=env.get("LATEST_JSON_URL") or None,
        spots_path=Path(spots_path),
        out_dir=Path(out_dir),
    )


def resolve_slot(requested: str, now: datetime) -> str:
    if requested == "auto":
        return "day" if now.hour < _NIGHT_STARTS_AT_HOUR else "night"
    if requested in SLOTS:
        return requested
    raise ConfigError(f"unknown slot: {requested!r}")


def run(
    settings: Settings,
    now: datetime,
    slot: str,
    *,
    fetch_condition=weather.fetch_condition,
    fetch_recent=history.fetch_recent_ids,
    generate=cf_client.generate_image,
    notify=notifier.notify_failure,
    rng: random.Random | None = None,
) -> int:
    """Generate one wallpaper. `now` must be in KST. Returns the process exit code."""
    today = now.date()
    rng = rng or random.SystemRandom()
    spots = spot_selector.load_spots(settings.spots_path)
    recent = fetch_recent(settings.latest_json_url) if settings.latest_json_url else []
    spot = spot_selector.choose_spot(spots, recent, rng)
    seed = rng.randrange(_SEED_LIMIT)
    sky_side = rng.choice(SKY_SIDES)
    moon = moon_phase.phase_of(now)
    condition = fetch_condition(now)
    season = prompt_builder.season_of(today)
    prompt = prompt_builder.build_prompt(spot, slot, season, condition, _opposite_side(sky_side))
    logger.info("slot=%s spot=%s weather=%s season=%s", slot, spot.id, condition, season)

    try:
        raw = generate(
            prompt,
            account_id=settings.account_id,
            api_token=settings.api_token,
            model=settings.model,
            width=GEN_WIDTH,
            height=GEN_HEIGHT,
            seed=seed,
        )
        jpeg = image_post.to_wallpaper(
            raw,
            WALLPAPER_WIDTH,
            WALLPAPER_HEIGHT,
            _visible_moon(slot, condition, moon, sky_side),
            precipitation_for(condition, seed),
        )
    except (cf_client.GenerationError, image_post.ImageProcessingError) as exc:
        logger.error("wallpaper generation failed: %s", exc)
        notify(
            settings.webhook_url, f"[daily-wallpaper] {today} {slot} ({spot.name_ko}) 실패: {exc}"
        )
        return 1

    _write_outputs(
        settings.out_dir,
        jpeg,
        {
            "slot": slot,
            "spot_id": spot.id,
            "spot_name_ko": spot.name_ko,
            "spot_area": spot.area,
            "season": season,
            "weather": condition,
            "model": settings.model,
            "seed": seed,
            "sky_side": sky_side,
            "moon_phase": moon,
            "generated_at": now.isoformat(),
            history.HISTORY_KEY: history.record(
                recent, spot.id, spot_selector.history_window(spots)
            ),
        },
    )
    return 0


def _opposite_side(side: str) -> str:
    """Waterfall streams go opposite the moon so the two never crowd the same side."""
    return next(other for other in SKY_SIDES if other != side)


def _visible_moon(slot: str, condition: str, phase: str, side: str) -> Moon | None:
    """The moon to paint: only at night, in weather that lets it be seen."""
    if slot != "night" or condition not in MOON_VISIBLE_CONDITIONS:
        return None
    return Moon(phase=phase, side=side)


def main(argv=None, env=None, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the daily landscape wallpaper.")
    parser.add_argument("--slot", choices=("auto", *SLOTS), default="auto")
    parser.add_argument("--out", type=Path, default=Path("site"))
    parser.add_argument("--spots", type=Path, default=DEFAULT_SPOTS_PATH)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    current = now if now is not None else datetime.now(KST)
    try:
        settings = load_settings(os.environ if env is None else env, args.spots, args.out)
        slot = resolve_slot(args.slot, current)
    except ConfigError as exc:
        logger.error("configuration error: %s", exc)
        return 2
    return run(settings, current, slot)


def _write_outputs(out_dir: Path, jpeg: bytes, metadata: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest.jpg").write_bytes(jpeg)
    (out_dir / "latest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())
