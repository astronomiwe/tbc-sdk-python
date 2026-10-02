"""Helpers for handling TBC Checkout callback payloads safely."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .exceptions import TBCCallbackError


def parse_callback(payload: Mapping[str, Any]) -> str:
    """Return the payment ID from a TBC callback payload.

    TBC callbacks are notifications, not payment confirmation. Fetch the payment with
    ``get_payment`` before fulfilling an order, and make fulfilment idempotent in the
    merchant application.
    """
    payment_id = payload.get("PaymentId")
    if not isinstance(payment_id, str) or not payment_id.strip():
        raise TBCCallbackError("TBC callback must contain a non-empty PaymentId")
    return payment_id
