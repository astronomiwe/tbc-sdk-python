import json
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from django.conf import settings
from django.test import RequestFactory
from fastapi import HTTPException
from starlette.requests import Request

from tbc_payments import TBCCallbackError
from tbc_payments.integrations.django import payment_id_from_request as django_payment_id
from tbc_payments.integrations.fastapi import payment_id_from_request as fastapi_payment_id

if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")


def fastapi_request(body: bytes) -> Request:
    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body}

    receive_callable: Callable[[], Awaitable[dict[str, Any]]] = receive
    return Request(
        {
            "type": "http",
            "method": "POST",
            "headers": [(b"content-type", b"application/json")],
        },
        receive_callable,
    )


@pytest.mark.asyncio
async def test_fastapi_callback_adapter_returns_payment_id() -> None:
    request = fastapi_request(b'{"PaymentId":"payment-1"}')

    assert await fastapi_payment_id(request) == "payment-1"


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [b"not-json", b"{}", b"[]"])
async def test_fastapi_callback_adapter_rejects_invalid_body(body: bytes) -> None:
    with pytest.raises(HTTPException) as error:
        await fastapi_payment_id(fastapi_request(body))

    assert error.value.status_code == 400


def test_django_callback_adapter_returns_payment_id() -> None:
    request = RequestFactory().post(
        "/webhooks/tbc/",
        data=json.dumps({"PaymentId": "payment-1"}),
        content_type="application/json",
    )

    assert django_payment_id(request) == "payment-1"


@pytest.mark.parametrize("body", [b"not-json", b"{}", b"[]"])
def test_django_callback_adapter_rejects_invalid_body(body: bytes) -> None:
    request = RequestFactory().post("/webhooks/tbc/", data=body, content_type="application/json")

    with pytest.raises(TBCCallbackError):
        django_payment_id(request)
