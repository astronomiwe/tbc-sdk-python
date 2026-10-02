from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

import httpx

from .exceptions import TBCAPIError, TBCAuthenticationError

BASE_URL = "https://api.tbcbank.ge/v1"
SANDBOX_URL = "https://test-api.tbcbank.ge/v1"


@dataclass(frozen=True, slots=True)
class TBCConfig:
    api_key: str
    client_id: str
    client_secret: str
    base_url: str = BASE_URL
    timeout: float = 15.0
    max_retries: int = 2

    def __post_init__(self) -> None:
        if not all((self.api_key, self.client_id, self.client_secret)):
            raise ValueError("api_key, client_id and client_secret are required")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")


def parse_response(response: httpx.Response) -> dict[str, Any]:
    if response.is_success and not response.content:
        return {}
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}
    if response.is_error:
        error_cls = TBCAuthenticationError if response.status_code in (401, 403) else TBCAPIError
        raise error_cls(response.status_code, payload)
    if not isinstance(payload, dict):
        raise TBCAPIError(response.status_code, {"detail": "Expected JSON object from TBC API"})
    return payload


def retry_delay(attempt: int) -> float:
    return float(min(2.0, 0.25 * (2**attempt)) + secrets.randbelow(101) / 1000)


def should_retry_status(status: int) -> bool:
    return status == 429 or 500 <= status <= 599
