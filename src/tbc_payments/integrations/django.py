"""Django helpers. Install with ``pip install tbc-payments[django]``."""

from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest

from ..exceptions import TBCCallbackError
from ..webhooks import parse_callback


def payment_id_from_request(request: HttpRequest) -> str:
    """Read and validate a TBC callback JSON body from a Django request.

    Raise :class:`TBCCallbackError` for malformed input; a caller can return HTTP 400.
    A valid notification still needs server-side payment lookup and idempotent fulfilment.
    """
    try:
        payload: Any = json.loads(request.body)
    except (TypeError, ValueError) as exc:
        raise TBCCallbackError("TBC callback body must be JSON") from exc
    if not isinstance(payload, dict):
        raise TBCCallbackError("TBC callback body must be a JSON object")
    return parse_callback(payload)
