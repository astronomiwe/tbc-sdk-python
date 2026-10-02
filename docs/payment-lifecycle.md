# Payment lifecycle

1. Create a `PaymentRequest` with a unique `merchant_payment_id`.
2. Redirect the buyer to `payment.approval_url`.
3. Receive a callback notification.
4. Fetch the payment from TBC using its `pay_id`.
5. Fulfil the order only for the final successful status, and only once.

Never treat a browser redirect or callback as payment confirmation on its own. The
callback is a prompt to fetch the authoritative payment state from TBC.

```python
payment = tbc.get_payment(payment_id)
if payment.status == "Succeeded":
    orders.mark_paid_once(payment.pay_id)
```

`mark_paid_once` must be atomic in your database. A unique constraint on the TBC
payment ID is a simple, effective choice.

## Retries

The SDK retries safe reads and token requests conservatively. It does not retry
create, cancel, completion, or recurring-payment requests: a network timeout for a
money-moving request is ambiguous and must be reconciled using your merchant order ID
or a subsequent payment lookup.
