"""Errors raised by :mod:`tbc_payments`."""

from __future__ import annotations

from typing import Any


class TBCError(Exception):
    """Base class for all SDK errors."""


class TBCNetworkError(TBCError):
    """The API could not be reached or did not respond in time."""


class TBCAPIError(TBCError):
    """An error response returned by TBC Checkout."""

    def __init__(self, status_code: int, payload: Any = None) -> None:
        self.status_code = status_code
        self.payload = payload
        if isinstance(payload, dict):
            message = payload.get("developerMessage") or payload.get("detail") or payload.get("title")
        else:
            message = None
        super().__init__(message or f"TBC API returned HTTP {status_code}")


class TBCAuthenticationError(TBCAPIError):
    """Credentials or the current access token were rejected."""
