"""Shared validation for public SDK inputs."""

from __future__ import annotations

from urllib.parse import urlsplit


def require_identifier(value: str, name: str) -> str:
    """Validate an API identifier before it is used in a URL path."""
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be a non-empty string without surrounding whitespace")
    return value


def require_absolute_http_url(value: str, name: str) -> str:
    """Validate an absolute HTTP(S) URL used by a payment request."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(f"{name} must be an absolute HTTP(S) URL")
    return value


def validate_extra_pair(extra: str | None, extra2: str | None, operation: str) -> None:
    """Validate the optional paired split-payment correlation fields."""
    if (extra is None) != (extra2 is None):
        raise ValueError(f"extra and extra2 must be supplied together for {operation}")
    for name, value, maximum_length in (("extra", extra, 25), ("extra2", extra2, 52)):
        if value is not None and (not value or len(value) > maximum_length or not value.isascii()):
            raise ValueError(
                f"{name} must be non-empty ASCII and no longer than {maximum_length} characters"
            )
