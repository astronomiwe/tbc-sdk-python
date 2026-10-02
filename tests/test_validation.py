import httpx
import pytest

from tbc_payments import Amount, AsyncTBCClient, PaymentRequest, TBCClient


def unexpected_request(_: httpx.Request) -> httpx.Response:
    pytest.fail("validation must fail before an HTTP request is made")


@pytest.mark.parametrize(
    "operation",
    [
        lambda client: client.get_payment(""),
        lambda client: client.cancel_payment(" payment-1"),
        lambda client: client.complete_payment("payment-1 ", "1"),
        lambda client: client.delete_recurring_payment(""),
        lambda client: client.execute_recurring_payment(" recurring-1", Amount("1")),
        lambda client: client.execute_recurring_payment("recurring-1", Amount("1"), extra="order"),
        lambda client: client.execute_recurring_payment(
            "recurring-1", Amount("1"), merchant_payment_id=" "
        ),
    ],
)
def test_sync_client_rejects_invalid_public_inputs_before_network(
    operation: object,
) -> None:
    with (
        TBCClient(
            "key", "id", "secret", transport=httpx.MockTransport(unexpected_request)
        ) as client,
        pytest.raises(ValueError),
    ):
        operation(client)  # type: ignore[operator]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    [
        lambda client: client.get_payment(""),
        lambda client: client.cancel_payment("payment-1", extra="order"),
        lambda client: client.complete_payment(" payment-1", "1"),
        lambda client: client.delete_recurring_payment(""),
        lambda client: client.execute_recurring_payment("recurring-1", Amount("1"), extra2="flow"),
    ],
)
async def test_async_client_rejects_invalid_public_inputs_before_network(
    operation: object,
) -> None:
    async with AsyncTBCClient(
        "key", "id", "secret", transport=httpx.MockTransport(unexpected_request)
    ) as client:
        with pytest.raises(ValueError):
            await operation(client)  # type: ignore[operator]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"return_url": "https://"},
        {"callback_url": "/webhooks/tbc"},
        {"merchant_payment_id": " "},
    ],
)
def test_payment_request_rejects_invalid_public_strings(kwargs: dict[str, str]) -> None:
    values = {"return_url": "https://merchant.example/return", **kwargs}

    with pytest.raises(ValueError):
        PaymentRequest(Amount("1"), **values)
