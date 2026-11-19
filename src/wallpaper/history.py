"""Which spots were used recently, carried from one run to the next via the deployed latest.json."""

import logging
import time

import requests

logger = logging.getLogger(__name__)

HISTORY_KEY = "recent_spot_ids"


def fetch_recent_ids(url: str, get=requests.get, timeout: int = 10) -> list[str]:
    """Recent spot ids (newest first) from the deployed latest.json.

    Any failure (first deploy, network, unexpected format) degrades to an empty list, because a
    missing history must never block image generation.
    """
    try:
        response = get(
            url,
            params={"t": int(time.time())},  # Pages sits behind a CDN; avoid a stale copy
            headers={"Cache-Control": "no-cache"},
            timeout=timeout,
        )
        response.raise_for_status()
        recent = response.json()[HISTORY_KEY]
        if not isinstance(recent, list) or not all(isinstance(item, str) for item in recent):
            raise TypeError(f"{HISTORY_KEY} is not a list of strings")
        return recent
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        logger.warning("spot history unavailable (%s); choosing without it", type(exc).__name__)
        return []


def record(recent: list[str], spot_id: str, limit: int) -> list[str]:
    """`spot_id` becomes the newest entry; older entries follow, without duplicates, up to limit."""
    return [spot_id, *(item for item in recent if item != spot_id)][:limit]
