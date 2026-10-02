"""FastAPI helpers. Install with ``pip install tbc-payments[fastapi]``."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request

from ..exceptions import TBCCallbackError
from ..webhooks import parse_callback


async def payment_id_from_request(request: Request) -> str:
    """Read and validate a TBC callback JSON body from a FastAPI request.

    The helper only extracts the payment ID. The view must fetch the payment from TBC
    and fulfil its order idempotently before returning HTTP 200.
    """
    try:
        payload: Any = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="TBC callback body must be JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="TBC callback body must be a JSON object")
    try:
        return parse_callback(payload)
    except TBCCallbackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
