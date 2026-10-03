from decimal import Decimal

import pytest

from tbc_payments import (
    Amount,
    CompletionResult,
    Currency,
    InstallmentProduct,
    Payment,
    PaymentMethod,
    PaymentRequest,
    RecurringCard,
    TBCResponseError,
)


def test_amount_serializes_optional_fields() -> None:
    amount = Amount("12.50", Currency.USD, subtotal="10", tax="1.50", shipping="1")

    assert amount.to_dict() == {
        "currency": "USD",
        "total": 12.5,
        "subTotal": 10.0,
        "tax": 1.5,
        "shipping": 1.0,
    }


@pytest.mark.parametrize("value", ["-1", "NaN", "Infinity", "1.001"])
def test_amount_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        Amount(value)


def test_installment_product_requires_positive_quantity() -> None:
    with pytest.raises(ValueError, match="positive"):
        InstallmentProduct("1", 0)


@pytest.mark.parametrize("quantity", [True, False])
def test_installment_product_rejects_boolean_quantity(quantity: bool) -> None:
    with pytest.raises(TypeError, match="integer"):
        InstallmentProduct("1", quantity)


def test_installment_product_rejects_float_quantity() -> None:
    with pytest.raises(TypeError, match="integer"):
        InstallmentProduct("1", 1.5)


def test_installment_product_accepts_positive_integer_quantity() -> None:
    product = InstallmentProduct("1", 1)
    assert product.quantity == 1
    assert product.to_dict() == {"price": 1.0, "quantity": 1}


def test_payment_request_serializes_all_optional_fields() -> None:
    request = PaymentRequest(
        amount=Amount("10"),
        return_url="https://merchant.example/return",
        callback_url="https://merchant.example/callback",
        merchant_payment_id="order-1",
        methods=(PaymentMethod.CARD,),
        description="Coffee",
        expiration_minutes=30,
        pre_auth=True,
        save_card=True,
        save_card_to_date="1227",
        language="EN",
        user_ip_address="127.0.0.1",
        extra="order",
        extra2="subscription",
        skip_info_message=False,
    )

    assert request.to_dict() == {
        "amount": {"currency": "GEL", "total": 10.0},
        "returnurl": "https://merchant.example/return",
        "callbackUrl": "https://merchant.example/callback",
        "merchantPaymentId": "order-1",
        "methods": [5],
        "description": "Coffee",
        "expirationMinutes": 30,
        "preAuth": True,
        "saveCard": True,
        "saveCardToDate": "1227",
        "language": "EN",
        "userIpAddress": "127.0.0.1",
        "extra": "order",
        "extra2": "subscription",
        "skipInfoMessage": False,
    }


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"language": "RU"}, "language"),
        ({"extra": "ქართული"}, "ASCII"),
        ({"extra2": "x" * 53}, "extra2"),
        ({"save_card_to_date": "1327"}, "MMYY"),
        ({"description": "x" * 31}, "description"),
        ({"expiration_minutes": 0}, "expiration"),
    ],
)
def test_payment_request_rejects_invalid_optional_fields(
    kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        PaymentRequest(Amount("1"), "https://merchant.example/return", **kwargs)


@pytest.mark.parametrize("invalid_method", [999, 0, -1, 3.14, "CARD", None])
def test_payment_request_rejects_invalid_payment_method(invalid_method: object) -> None:
    with pytest.raises(TypeError, match="PaymentMethod"):
        PaymentRequest(Amount("1"), "https://merchant.example/return", methods=(invalid_method,))  # type: ignore[arg-type]


def test_payment_request_accepts_valid_payment_method_enum_member() -> None:
    request = PaymentRequest(
        amount=Amount("10"),
        return_url="https://merchant.example/return",
        methods=(PaymentMethod.CARD, PaymentMethod.APPLE_PAY),
    )
    assert request.methods == (PaymentMethod.CARD, PaymentMethod.APPLE_PAY)


def test_payment_response_parses_links_recurring_card_and_decimals() -> None:
    payment = Payment.from_dict(
        {
            "payId": "payment-1",
            "status": "Succeeded",
            "amount": "12.50",
            "currency": "GEL",
            "links": [
                {"uri": "https://checkout.example", "method": "REDIRECT", "rel": "approval_url"}
            ],
            "confirmedAmount": "10.00",
            "returnedAmount": 2.5,
            "recurringCard": {"recId": "rec-1", "cardMask": "****1111", "expirtyDate": "1227"},
            "RRN": "rrn-1",
        }
    )

    assert payment.approval_url == "https://checkout.example"
    assert payment.confirmed_amount == Decimal("10.00")
    assert payment.returned_amount == Decimal("2.5")
    assert payment.recurring_card == RecurringCard("rec-1", "****1111", "1227")
    assert payment.rrn == "rrn-1"


@pytest.mark.parametrize(
    "response",
    [
        {"status": "Created"},
        {"payId": "payment-1"},
        {"payId": "payment-1", "status": "Created", "links": "invalid"},
        {"payId": "payment-1", "status": "Created", "amount": "NaN"},
        {
            "payId": "payment-1",
            "status": "Created",
            "recurringCard": {"cardMask": "****1111"},
        },
    ],
)
def test_payment_response_validation_raises_public_error(response: dict[str, object]) -> None:
    with pytest.raises(TBCResponseError):
        Payment.from_dict(response)


def test_completion_response_requires_status() -> None:
    with pytest.raises(TBCResponseError, match="status"):
        CompletionResult.from_dict("payment-1", {"amount": 1})
