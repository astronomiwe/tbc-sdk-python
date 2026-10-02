# API reference

## Clients

- `TBCClient`: synchronous context-managed client.
- `AsyncTBCClient`: asynchronous context-managed client.

Both expose the same payment operations:

| Method | Purpose |
| --- | --- |
| `create_payment(request)` | Start a checkout payment. |
| `get_payment(pay_id)` | Fetch authoritative payment state. |
| `cancel_payment(pay_id, amount=None)` | Cancel or return a payment. |
| `complete_payment(pay_id, amount)` | Complete a pre-authorisation. |
| `execute_recurring_payment(recurring_id, amount)` | Charge a saved-card registration. |
| `delete_recurring_payment(recurring_id)` | Delete a saved-card registration. |

## Exceptions

- `TBCAuthenticationError`: TBC rejected credentials or an access token.
- `TBCAPIError`: TBC returned an error HTTP response.
- `TBCNetworkError`: the request could not be completed.
- `TBCResponseError`: a successful response did not match the documented schema.
- `TBCCallbackError`: the merchant callback payload lacks a valid `PaymentId`.

## Input validation

Public client operations reject empty or whitespace-padded payment and recurring IDs
before sending an HTTP request. Payment request URLs must be absolute HTTP(S) URLs.
Split-cancellation and recurring-payment `extra` and `extra2` fields must be supplied
together, use ASCII, and stay within TBC's documented length limits.
