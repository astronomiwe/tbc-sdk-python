"""Immutable request and response models for TBC Checkout."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any


class Currency(str, Enum):
    GEL = "GEL"
    USD = "USD"
    EUR = "EUR"


class PaymentMethod(IntEnum):
    WEB_QR_BNPL = 4
    CARD = 5
    INTERNET_BANK = 7
    INSTALLMENT = 8
    APPLE_PAY = 9
    GOOGLE_PAY = 14


class PaymentStatus(str, Enum):
    CREATED = "Created"
    PROCESSING = "Processing"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    EXPIRED = "Expired"
    WAITING_CONFIRM = "WaitingConfirm"
    CANCEL_PAYMENT_PROCESSING = "CancelPaymentProcessing"
    PAYMENT_COMPLETION_PROCESSING = "PaymentCompletionProcessing"
    RETURNED = "Returned"
    PARTIAL_RETURNED = "PartialReturned"


def _number(value: Decimal | float | str) -> float:
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValueError("Amount must be a finite, non-negative number")
    if amount.as_tuple().exponent < -2:
        raise ValueError("Amount cannot have more than two decimal places")
    return float(amount.quantize(Decimal("0.01")))


@dataclass(frozen=True, slots=True)
class Amount:
    total: Decimal | int | float | str
    currency: Currency = Currency.GEL
    subtotal: Decimal | int | float | str | None = None
    tax: Decimal | int | float | str | None = None
    shipping: Decimal | int | float | str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.currency, Currency):
            raise TypeError("currency must be a Currency value")
        _number(self.total)
        for value in (self.subtotal, self.tax, self.shipping):
            if value is not None:
                _number(value)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"currency": self.currency.value, "total": _number(self.total)}
        for field_name, api_name in (("subtotal", "subTotal"), ("tax", "tax"), ("shipping", "shipping")):
            value = getattr(self, field_name)
            if value is not None:
                result[api_name] = _number(value)
        return result


@dataclass(frozen=True, slots=True)
class InstallmentProduct:
    """A product financed through TBC Installment (payment method 8)."""

    price: Decimal | float | str
    quantity: int
    name: str | None = None

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("installment product quantity must be positive")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"price": _number(self.price), "quantity": self.quantity}
        if self.name is not None:
            data["name"] = self.name
        return data


@dataclass(frozen=True, slots=True)
class PaymentRequest:
    amount: Amount
    return_url: str
    callback_url: str | None = None
    merchant_payment_id: str | None = None
    methods: tuple[PaymentMethod, ...] = ()
    description: str | None = None
    expiration_minutes: int | None = None
    pre_auth: bool | None = None
    save_card: bool | None = None
    save_card_to_date: str | None = None
    language: str | None = None
    user_ip_address: str | None = None
    extra: str | None = None
    extra2: str | None = None
    skip_info_message: bool | None = None
    installment_products: tuple[InstallmentProduct, ...] = ()

    def __post_init__(self) -> None:
        if not self.return_url.startswith(("https://", "http://")):
            raise ValueError("return_url must be an absolute HTTP(S) URL")
        if self.expiration_minutes is not None and self.expiration_minutes <= 0:
            raise ValueError("expiration_minutes must be positive")
        if self.description is not None and len(self.description) > 30:
            raise ValueError("description cannot exceed 30 characters")
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("methods must not contain duplicates")
        if self.language is not None and self.language not in {"KA", "EN"}:
            raise ValueError("language must be KA or EN")
        if self.extra is not None and (len(self.extra) > 25 or not self.extra.isascii()):
            raise ValueError("extra must be ASCII and no longer than 25 characters")
        if self.extra2 is not None and (len(self.extra2) > 52 or not self.extra2.isascii()):
            raise ValueError("extra2 must be ASCII and no longer than 52 characters")
        if self.save_card_to_date is not None and not re.fullmatch(
            r"(0[1-9]|1[0-2])\d{2}", self.save_card_to_date
        ):
            raise ValueError("save_card_to_date must use MMYY format")
        uses_installment = PaymentMethod.INSTALLMENT in self.methods
        if uses_installment and not self.installment_products:
            raise ValueError("installment_products are required for installment payments")
        if uses_installment and self.amount.currency is not Currency.GEL:
            raise ValueError("installment payments are available only in GEL")
        if self.installment_products:
            products_total = sum(
                Decimal(str(item.price)) * item.quantity for item in self.installment_products
            ).quantize(Decimal("0.01"))
            if products_total != Decimal(str(self.amount.total)).quantize(Decimal("0.01")):
                raise ValueError("installment product total must equal payment total")
        incompatible_with_save_card = {PaymentMethod.WEB_QR_BNPL, PaymentMethod.INSTALLMENT, PaymentMethod.APPLE_PAY}
        if self.save_card and incompatible_with_save_card.intersection(self.methods):
            raise ValueError("save_card is incompatible with Web QR, installment, and Apple Pay")
        if Decimal(str(self.amount.total)) == 0 and not self.save_card:
            raise ValueError("zero amount is allowed only when save_card is enabled")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"amount": self.amount.to_dict(), "returnurl": self.return_url}
        fields = {
            "callbackUrl": self.callback_url, "merchantPaymentId": self.merchant_payment_id,
            "description": self.description, "expirationMinutes": self.expiration_minutes,
            "preAuth": self.pre_auth, "saveCard": self.save_card, "saveCardToDate": self.save_card_to_date,
            "language": self.language, "userIpAddress": self.user_ip_address, "extra": self.extra, "extra2": self.extra2,
            "skipInfoMessage": self.skip_info_message,
        }
        data.update({key: value for key, value in fields.items() if value is not None})
        if self.methods:
            data["methods"] = [int(method) for method in self.methods]
        if self.installment_products:
            data["installmentProducts"] = [product.to_dict() for product in self.installment_products]
        return data


@dataclass(frozen=True, slots=True)
class PaymentLink:
    uri: str
    method: str
    rel: str


@dataclass(frozen=True, slots=True)
class RecurringCard:
    recurring_id: str
    card_mask: str | None = None
    expiry_date: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecurringCard:
        return cls(data["recId"], data.get("cardMask"), data.get("expiryDate") or data.get("expirtyDate"))


@dataclass(frozen=True, slots=True)
class CompletionResult:
    """Result returned after completing a pre-authorized payment."""

    pay_id: str
    status: str
    amount: Decimal | None = None
    confirmed_amount: Decimal | None = None
    http_status_code: int | None = None
    developer_message: str | None = None
    user_message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, pay_id: str, data: dict[str, Any]) -> CompletionResult:
        def decimal_value(name: str) -> Decimal | None:
            value = data.get(name)
            return Decimal(str(value)) if value is not None else None
        return cls(pay_id, data["status"], decimal_value("amount"), decimal_value("confirmedAmount"),
                   data.get("httpStatusCode"), data.get("developerMessage"), data.get("userMessage"), data)


@dataclass(frozen=True, slots=True)
class Payment:
    pay_id: str
    status: str
    amount: Decimal | None = None
    currency: str | None = None
    links: tuple[PaymentLink, ...] = field(default_factory=tuple)
    transaction_id: str | None = None
    recurring_id: str | None = None
    pre_auth: bool | None = None
    confirmed_amount: Decimal | None = None
    returned_amount: Decimal | None = None
    payment_method: int | None = None
    recurring_card: RecurringCard | None = None
    rrn: str | None = None
    result_code: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def approval_url(self) -> str | None:
        """Checkout redirect URL, if one was returned."""
        return next((link.uri for link in self.links if link.rel == "approval_url"), None)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Payment:
        links = tuple(PaymentLink(**link) for link in (data.get("links") or []))
        amount = data.get("amount")
        decimal_value = lambda key: Decimal(str(data[key])) if data.get(key) is not None else None
        recurring_card = data.get("recurringCard")
        return cls(data["payId"], data["status"], Decimal(str(amount)) if amount is not None else None,
                   data.get("currency"), links, data.get("transactionId"), data.get("recId"),
                   data.get("preAuth"), decimal_value("confirmedAmount"), decimal_value("returnedAmount"),
                   data.get("paymentMethod"), RecurringCard.from_dict(recurring_card) if recurring_card else None,
                   data.get("rrn") or data.get("RRN"), data.get("resultCode"), data)
