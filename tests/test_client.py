import json

import httpx
import pytest

from tbc_payments import (
    Amount,
    AsyncTBCClient,
    Currency,
    InstallmentProduct,
    PaymentMethod,
    PaymentRequest,
    TBCAPIError,
    TBCClient,
)


def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/access-token"):
        assert request.headers["apikey"] == "key"
        return httpx.Response(200, json={"access_token": "token"})
    if request.url.path.endswith("/tpay/payments") and request.method == "POST":
        assert request.headers["authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json={
                "payId": "p-1",
                "status": "Created",
                "amount": 12.5,
                "currency": "GEL",
                "links": [
                    {
                        "uri": "https://checkout.example/p-1",
                        "method": "REDIRECT",
                        "rel": "approval_url",
                    }
                ],
            },
        )
    if request.url.path.endswith("/delete"):
        assert request.headers["authorization"] == "Bearer token"
        return httpx.Response(200)
    return httpx.Response(404, json={"detail": "not found"})


def request() -> PaymentRequest:
    return PaymentRequest(
        Amount("12.50", Currency.GEL),
        "https://merchant.example/return",
        methods=(PaymentMethod.CARD,),
    )


def test_sync_payment_and_serialization() -> None:
    transport = httpx.MockTransport(handler)
    with TBCClient("key", "id", "secret", transport=transport) as client:
        payment = client.create_payment(request())
    assert payment.pay_id == "p-1"
    assert payment.approval_url == "https://checkout.example/p-1"
    assert request().to_dict()["amount"]["total"] == 12.5


@pytest.mark.asyncio
async def test_async_payment() -> None:
    transport = httpx.MockTransport(handler)
    async with AsyncTBCClient("key", "id", "secret", transport=transport) as client:
        payment = await client.create_payment(request())
    assert payment.status == "Created"


@pytest.mark.asyncio
async def test_async_cancel_and_completion_contracts() -> None:
    def async_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("access-token"):
            return httpx.Response(200, json={"access_token": "token"})
        if request.url.path.endswith("cancel"):
            return httpx.Response(200)
        if request.url.path.endswith("completion"):
            return httpx.Response(200, json={"status": "Succeeded", "amount": 10})
        return httpx.Response(404)

    async with AsyncTBCClient(
        "key", "id", "secret", transport=httpx.MockTransport(async_handler)
    ) as client:
        assert await client.cancel_payment("p-1") is None
        assert (await client.complete_payment("p-1", "10")).pay_id == "p-1"


def test_error_is_structured() -> None:
    def unauthorized(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "bad key"})

    with (
        TBCClient("key", "id", "secret", transport=httpx.MockTransport(unauthorized)) as client,
        pytest.raises(TBCAPIError) as error,
    ):
        client.get_payment("payment")
    assert error.value.status_code == 401


def test_request_validation() -> None:
    with pytest.raises(ValueError, match="absolute"):
        PaymentRequest(Amount(1), "/relative")
    with pytest.raises(ValueError, match="duplicates"):
        PaymentRequest(
            Amount(1), "https://example.com", methods=(PaymentMethod.CARD, PaymentMethod.CARD)
        )
    with pytest.raises(ValueError, match="two decimal"):
        Amount("1.005")


def test_installment_payload_and_validation() -> None:
    payment = PaymentRequest(
        Amount("100.00"),
        "https://example.com/return",
        methods=(PaymentMethod.INSTALLMENT,),
        installment_products=(InstallmentProduct("50", 2, "Product"),),
        skip_info_message=True,
    )
    assert payment.to_dict()["installmentProducts"] == [
        {"price": 50.0, "quantity": 2, "name": "Product"}
    ]
    with pytest.raises(ValueError, match="installment_products"):
        PaymentRequest(Amount(100), "https://example.com", methods=(PaymentMethod.INSTALLMENT,))


def test_delete_recurring_payment() -> None:
    with TBCClient("key", "id", "secret", transport=httpx.MockTransport(handler)) as client:
        assert client.delete_recurring_payment("rec-1") is None


def test_cancel_split_and_completion_contracts() -> None:
    calls: list[httpx.Request] = []

    def payment_handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("access-token"):
            return httpx.Response(200, json={"access_token": "token", "expires_in": 86400})
        if request.url.path.endswith("cancel"):
            return httpx.Response(200)
        if request.url.path.endswith("completion"):
            return httpx.Response(
                200,
                json={
                    "status": "Succeeded",
                    "amount": 10,
                    "confirmedAmount": 0.1,
                    "httpStatusCode": 200,
                },
            )
        return httpx.Response(404)

    with TBCClient("key", "id", "secret", transport=httpx.MockTransport(payment_handler)) as client:
        assert client.cancel_payment("p-1", "2.00", extra="GE00", extra2="2.00") is None
        completion = client.complete_payment("p-1", "0.10")
    assert completion.pay_id == "p-1"
    assert completion.confirmed_amount is not None and str(completion.confirmed_amount) == "0.1"
    assert json.loads(calls[1].content) == {"amount": 2.0, "extra": "GE00", "extra2": "2.00"}


def test_recurring_extra_fields_are_sent() -> None:
    def recurring_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("access-token"):
            return httpx.Response(200, json={"access_token": "token"})
        if request.url.path.endswith("execution"):
            assert json.loads(request.content)["extra"] == "order"
            assert json.loads(request.content)["extra2"] == "subscription"
            return httpx.Response(200, json={"payId": "p-2", "status": "Succeeded"})
        return httpx.Response(404)

    with TBCClient(
        "key", "id", "secret", transport=httpx.MockTransport(recurring_handler)
    ) as client:
        assert (
            client.execute_recurring_payment(
                "rec-1", Amount("1"), extra="order", extra2="subscription"
            ).pay_id
            == "p-2"
        )


def test_get_retries_once_with_refreshed_token_after_unauthorized() -> None:
    tokens = iter(["expired", "fresh"])
    received_tokens: list[str] = []

    def refresh_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("access-token"):
            return httpx.Response(200, json={"access_token": next(tokens), "expires_in": 86400})
        received_tokens.append(request.headers["authorization"])
        if len(received_tokens) == 1:
            return httpx.Response(401, json={"detail": "expired"})
        return httpx.Response(200, json={"payId": "p-1", "status": "Succeeded"})

    with TBCClient("key", "id", "secret", transport=httpx.MockTransport(refresh_handler)) as client:
        assert client.get_payment("p-1").status == "Succeeded"
    assert received_tokens == ["Bearer expired", "Bearer fresh"]
