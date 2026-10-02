import pytest

from tbc_payments import TBCCallbackError, parse_callback


def test_parse_callback_returns_payment_id() -> None:
    assert parse_callback({"PaymentId": "payment-1"}) == "payment-1"


@pytest.mark.parametrize("payload", [{}, {"PaymentId": ""}, {"PaymentId": 1}])
def test_parse_callback_rejects_invalid_payload(payload: dict[str, object]) -> None:
    with pytest.raises(TBCCallbackError, match="PaymentId"):
        parse_callback(payload)
