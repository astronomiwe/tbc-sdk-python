# Framework examples

Install an adapter extra first:

```bash
pip install "tbc-payments[fastapi]"
# or
pip install "tbc-payments[django]"
```

Set `TBC_API_KEY`, `TBC_CLIENT_ID`, and `TBC_CLIENT_SECRET` in the runtime
environment. The examples intentionally do not include credentials, database models,
or fulfilment logic; implement idempotent order updates in your own transaction.
