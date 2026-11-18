"""Failure notification through a Discord webhook. Never raises: it must not mask the real error."""

import logging

import requests

logger = logging.getLogger(__name__)

# Discord rejects messages over 2000 characters.
MESSAGE_LIMIT = 1900


def notify_failure(webhook_url: str | None, message: str, post=requests.post) -> bool:
    """Send the message; return True only if Discord accepted it."""
    if not webhook_url:
        return False
    try:
        response = post(webhook_url, json={"content": message[:MESSAGE_LIMIT]}, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        # Log only the exception type: the message of a requests error contains the webhook URL.
        logger.warning("failure notification was not delivered (%s)", type(exc).__name__)
        return False
    return True
