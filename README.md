# tbc-payments

[![PyPI](https://img.shields.io/pypi/v/tbc-payments.svg)](https://pypi.org/project/tbc-payments/)
[![Python](https://img.shields.io/pypi/pyversions/tbc-payments.svg)](https://pypi.org/project/tbc-payments/)
[![CI](https://github.com/astronomiwe/tbc-sdk-python/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/astronomiwe/tbc-sdk-python/actions/workflows/ci.yml)
[![Documentation](https://github.com/astronomiwe/tbc-sdk-python/actions/workflows/docs.yml/badge.svg?branch=master)](https://astronomiwe.github.io/tbc-sdk-python/)
[![License](https://img.shields.io/pypi/l/tbc-payments.svg)](LICENSE)

`tbc-payments` is a small, typed Python client for [TBC Checkout](https://developers.tbcbank.ge/docs/checkout-api-overview). It helps a backend create a checkout session, redirect the customer to TBC's payment page, and later verify or manage the payment.

It has synchronous and asynchronous clients with the same API. The package manages access tokens and HTTP connections; it never handles card details.

Full guides for callbacks, FastAPI, Django, recurring payments, sandbox operations, and
the API are available in the [documentation](https://astronomiwe.github.io/tbc-sdk-python/).

## What it supports

- Creating and looking up Checkout payments.
- Cancelling payments and completing pre-authorizations.
- Creating and deleting recurring-payment registrations.
- TBC Installment requests.
- Production and sandbox URLs.
- Typed models, structured API errors, timeouts, and conservative retries.

## Installation

```bash
pip install tbc-payments
```

Python 3.10 or newer is required.

## Create a payment

```python
from tbc_payments import Amount, PaymentMethod, PaymentRequest, TBCClient

payment_request = PaymentRequest(
    amount=Amount("49.90"),
    return_url="https://shop.example.com/payments/return",
    callback_url="https://shop.example.com/webhooks/tbc",
    merchant_payment_id="order-1842",
    methods=(PaymentMethod.CARD, PaymentMethod.APPLE_PAY),
)

with TBCClient("api-key", "client-id", "client-secret") as tbc:
    payment = tbc.create_payment(payment_request)

redirect_url = payment.approval_url
```

Redirect the customer to `redirect_url`. A `merchant_payment_id` should be unique in your system so an ambiguous request can be reconciled safely.

## Check the result

Treat the callback as a notification, not as confirmation that an order is paid. Return HTTP 200 promptly, then fetch the payment from TBC and fulfil the order only once.

```python
payment = tbc.get_payment(callback_payload["PaymentId"])
if payment.status == "Succeeded":
    fulfil_order_once(payment.pay_id)
```

## Async

```python
from tbc_payments import Amount, AsyncTBCClient, PaymentRequest

async with AsyncTBCClient("api-key", "client-id", "client-secret", sandbox=True) as tbc:
    payment = await tbc.create_payment(
        PaymentRequest(Amount("1.00"), "https://shop.example.com/payments/return")
    )
```

## FastAPI and Django

Optional adapters validate callback request bodies without taking ownership of your
application's client lifecycle or order database:

```bash
pip install "tbc-payments[fastapi]"
# or
pip install "tbc-payments[django]"
```

See the [framework guides](docs/integrations.md) and runnable
[examples](examples/README.md). A callback is only a notification: fetch the payment
from TBC and fulfil its order idempotently before returning HTTP 200.

## Installments and recurring payments

Use `PaymentMethod.INSTALLMENT` with products whose total matches the payment amount:

```python
from tbc_payments import InstallmentProduct, PaymentMethod

request = PaymentRequest(
    amount=Amount("100.00"),
    return_url="https://shop.example.com/payments/return",
    methods=(PaymentMethod.INSTALLMENT,),
    installment_products=(InstallmentProduct("50.00", 2, "Coffee maker"),),
)
```

For saved cards, enable `save_card=True` when creating the initial payment and store the returned `recurring_id`. Call `execute_recurring_payment` only after your business flow has established the necessary customer consent.

## Behaviour worth knowing

- Amounts may have at most two decimal places. Values are validated rather than silently rounded.
- Tokens are refreshed before expiry. A failed read may be retried; money-moving requests are not retried automatically.
- `cancel_payment` returns `None` after a successful `200`. `complete_payment` returns `CompletionResult`.
- `sandbox=True` uses `https://test-api.tbcbank.ge/v1`.

## Development

```bash
python -m pip install -e '.[dev]'
pre-commit install
pytest
ruff check .
ruff format --check .
mypy
bandit -c pyproject.toml -r src
pip-audit
```

Build the local documentation site with:

```bash
python -m pip install -e '.[docs]'
mkdocs serve
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) for contribution and vulnerability-reporting guidance.

## License

[MIT](LICENSE)
