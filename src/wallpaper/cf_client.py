"""Cloudflare Workers AI text-to-image client with a small, bounded retry policy."""

import base64
import logging
import time

import requests

from .config import MAX_ATTEMPTS

logger = logging.getLogger(__name__)

API_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 120


class GenerationError(RuntimeError):
    """Image generation failed for good (retries exhausted or a non-retryable error)."""


def generate_image(
    prompt: str,
    *,
    account_id: str,
    api_token: str,
    model: str,
    width: int,
    height: int,
    seed: int,
    max_attempts: int = MAX_ATTEMPTS,
    post=requests.post,
    sleep=time.sleep,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> bytes:
    """Return the generated image bytes.

    Retries only on network errors, HTTP 429 and HTTP 5xx; each retry uses a new seed.
    Error messages deliberately omit URLs and headers because the logs of a public repository
    are public.
    """
    url = API_URL.format(account_id=account_id, model=model)
    headers = {"Authorization": f"Bearer {api_token}"}
    last_error = "no attempt was made"

    for attempt in range(max_attempts):
        if attempt:
            sleep(RETRY_DELAY_SECONDS * attempt)
        form = {
            "prompt": (None, prompt),
            "width": (None, str(width)),
            "height": (None, str(height)),
            "seed": (None, str(seed + attempt)),
        }
        try:
            response = post(url, headers=headers, files=form, timeout=timeout)
        except requests.RequestException as exc:
            last_error = f"network error ({type(exc).__name__})"
        else:
            if response.status_code == 200:
                return _decode_image(response)
            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            if not _is_retryable(response.status_code):
                raise GenerationError(last_error)
        logger.warning("generation attempt %d/%d failed: %s", attempt + 1, max_attempts, last_error)

    raise GenerationError(f"gave up after {max_attempts} attempts; last error: {last_error}")


def _is_retryable(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


def _decode_image(response) -> bytes:
    try:
        return base64.b64decode(response.json()["result"]["image"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GenerationError(f"unexpected response shape ({type(exc).__name__})") from exc
