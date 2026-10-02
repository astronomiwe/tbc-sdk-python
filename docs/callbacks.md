# Callbacks and webhooks

TBC sends a JSON callback containing `PaymentId` when a payment reaches a final state.
Return HTTP 200 promptly, then look up the payment server-side before changing order
state.

```python
from tbc_payments import parse_callback

payment_id = parse_callback({"PaymentId": "tbc-payment-id"})
payment = tbc.get_payment(payment_id)
```

`parse_callback` validates only the shape of the payload. It is not cryptographic
verification and it does not imply that a payment succeeded. Make fulfilment
idempotent and verify the final status through `get_payment`.

Your callback URL must be configured in the TBC merchant dashboard before go-live.
