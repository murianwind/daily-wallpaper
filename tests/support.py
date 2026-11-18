"""Test doubles shared by the step definitions."""

import io

import requests
from PIL import Image


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("response has no JSON body")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class Recorder:
    """Callable that records every call and delegates to responder(call_number, *args, **kwargs)."""

    def __init__(self, responder):
        self._responder = responder
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self._responder(len(self.calls), *args, **kwargs)


def png_bytes(width, height, color=(120, 90, 60), mode="RGB"):
    buffer = io.BytesIO()
    Image.new(mode, (width, height), color).save(buffer, format="PNG")
    return buffer.getvalue()


def capture(func, *args, **kwargs):
    """Run func and return (result, error); exactly one of them is None."""
    try:
        return func(*args, **kwargs), None
    except Exception as exc:  # noqa: BLE001 - the scenarios inspect the exception
        return None, exc
