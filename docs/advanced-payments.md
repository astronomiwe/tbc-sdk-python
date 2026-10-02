# Recurring payments and pre-authorisation

## Pre-authorisation

Create a payment with `pre_auth=True`. Once your business process is ready to capture
funds, call `complete_payment(pay_id, amount)`. Use `cancel_payment` to cancel an
authorisation or return a payment according to the TBC API rules.

```python
completion = tbc.complete_payment(payment.pay_id, "49.90")
```

Do not automatically retry completion or cancellation after a timeout. First fetch
the payment state and reconcile it with your order record.

## Saved cards and recurring payments

Set `save_card=True` while creating the initial payment, then store the returned
`recurring_id` only after the payment flow is complete and customer consent has been
recorded. Execute later charges with:

```python
payment = tbc.execute_recurring_payment("recurring-id", Amount("9.99"))
```

Treat recurring IDs as sensitive merchant data and make each charge traceable through
your own merchant payment identifier.
