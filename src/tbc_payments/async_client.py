"""Asynchronous TBC Checkout client."""

from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from typing import Any

try:  # Python 3.11+
    from typing import Self
except ImportError:  # pragma: no cover - exercised on Python 3.10
    from typing_extensions import Self

import httpx

from ._base import SANDBOX_URL, TBCConfig, parse_response, retry_delay, should_retry_status
from .exceptions import TBCNetworkError
from .models import Amount, CompletionResult, Payment, PaymentRequest, _number


class AsyncTBCClient:
    """Async client. Use with ``async with`` so connections are always closed."""
    def __init__(self, api_key: str, client_id: str, client_secret: str, *, sandbox: bool = False, base_url: str | None = None, timeout: float = 15.0, max_retries: int = 2, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.config = TBCConfig(api_key, client_id, client_secret, base_url or (SANDBOX_URL if sandbox else "https://api.tbcbank.ge/v1"), timeout, max_retries)
        self._client = httpx.AsyncClient(base_url=self.config.base_url, timeout=timeout, transport=transport, headers={"apikey": api_key, "Accept": "application/json", "User-Agent": "tbc-payments-python/0.1.0"})
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()
    async def __aenter__(self) -> Self: return self
    async def __aexit__(self, *_: object) -> None: await self.aclose()
    async def aclose(self) -> None: await self._client.aclose()
    async def _request(self, method: str, path: str, *, json: dict[str, Any] | None = None, data: dict[str, str] | None = None, auth: bool = True, retryable: bool = False) -> dict[str, Any]:
        if auth: await self._ensure_token()
        for attempt in range(self.config.max_retries + 1):
            try: response = await self._client.request(method, path, json=json, data=data, headers={"Authorization": f"Bearer {self._token}"} if auth else {})
            except httpx.HTTPError as exc:
                if retryable and attempt < self.config.max_retries: await asyncio.sleep(retry_delay(attempt)); continue
                raise TBCNetworkError("TBC API request failed") from exc
            if retryable and should_retry_status(response.status_code) and attempt < self.config.max_retries: await asyncio.sleep(retry_delay(attempt)); continue
            if auth and retryable and response.status_code == 401 and attempt < self.config.max_retries:
                self._token = None
                await self._ensure_token()
                continue
            return parse_response(response)
        raise AssertionError("unreachable")
    async def _ensure_token(self) -> None:
        if self._token is None or time.monotonic() >= self._token_expires_at:
            async with self._token_lock:
                if self._token is None or time.monotonic() >= self._token_expires_at:
                    result = await self._request("POST", "/tpay/access-token", data={"client_id": self.config.client_id, "client_secret": self.config.client_secret}, auth=False, retryable=True)
                    self._token = result["access_token"]
                    self._token_expires_at = time.monotonic() + max(1, int(result.get("expires_in", 86400)) - 60)
    async def create_payment(self, request: PaymentRequest) -> Payment: return Payment.from_dict(await self._request("POST", "/tpay/payments", json=request.to_dict()))
    async def get_payment(self, pay_id: str) -> Payment: return Payment.from_dict(await self._request("GET", f"/tpay/payments/{pay_id}", retryable=True))
    async def cancel_payment(self, pay_id: str, amount: Decimal | float | str | None = None, *, extra: str | None = None, extra2: str | None = None) -> None:
        if (extra is None) != (extra2 is None):
            raise ValueError("extra and extra2 must be supplied together for split cancellation")
        body = {} if amount is None else {"amount": _number(amount)}
        if extra is not None:
            body.update({"extra": extra, "extra2": extra2})
        await self._request("POST", f"/tpay/payments/{pay_id}/cancel", json=body)
    async def complete_payment(self, pay_id: str, amount: Decimal | float | str) -> CompletionResult:
        return CompletionResult.from_dict(pay_id, await self._request("POST", f"/tpay/payments/{pay_id}/completion", json={"amount": _number(amount)}))
    async def delete_recurring_payment(self, recurring_id: str) -> None:
        await self._request("POST", f"/tpay/payments/{recurring_id}/delete", json={})
    async def execute_recurring_payment(self, recurring_id: str, amount: Amount, *, merchant_payment_id: str | None = None, pre_auth: bool | None = None, initiator: str | None = None, extra: str | None = None, extra2: str | None = None) -> Payment:
        body: dict[str, Any] = {"recId": recurring_id, "money": {"currency": amount.currency.value, "amount": _number(amount.total)}}
        for key, value in {"merchantPaymentId": merchant_payment_id, "preAuth": pre_auth, "initiator": initiator, "extra": extra, "extra2": extra2}.items():
            if value is not None: body[key] = value
        return Payment.from_dict(await self._request("POST", "/tpay/payments/execution", json=body))
