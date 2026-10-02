# tbc-payments

`tbc-payments` is a typed Python client for the TBC Checkout API. It supports
synchronous and asynchronous applications, manages access tokens, and deliberately
does not retry money-moving requests.

## Install

```bash
pip install tbc-payments
```

Use `tbc-payments[fastapi]` or `tbc-payments[django]` for the optional callback
adapters.

## Create a payment

```python
from tbc_payments import Amount, PaymentMethod, PaymentRequest, TBCClient

request = PaymentRequest(
    amount=Amount("49.90"),
    return_url="https://shop.example.com/payments/return",
    callback_url="https://shop.example.com/webhooks/tbc",
    merchant_payment_id="order-1842",
    methods=(PaymentMethod.CARD,),
)

with TBCClient("api-key", "client-id", "client-secret") as tbc:
    payment = tbc.create_payment(request)

redirect_url = payment.approval_url
```

Redirect the buyer to `redirect_url`. Keep `merchant_payment_id` unique: it is the
merchant-side correlation key for reconciling ambiguous requests.

## Async

```python
from tbc_payments import Amount, AsyncTBCClient, PaymentRequest

async with AsyncTBCClient("api-key", "client-id", "client-secret", sandbox=True) as tbc:
    payment = await tbc.create_payment(
        PaymentRequest(Amount("1.00"), "https://shop.example.com/payments/return")
    )
```

Continue with [the payment lifecycle](payment-lifecycle.md) before going live.
