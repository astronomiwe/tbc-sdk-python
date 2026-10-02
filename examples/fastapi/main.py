"""Run with: uvicorn main:app --reload after installing tbc-payments[fastapi]."""

from __future__ import annotations

import os

from fastapi import FastAPI, Request, Response

from tbc_payments import AsyncTBCClient
from tbc_payments.integrations.fastapi import payment_id_from_request

app = FastAPI()


@app.post("/webhooks/tbc")
async def tbc_callback(request: Request) -> Response:
    payment_id = await payment_id_from_request(request)
    async with AsyncTBCClient(
        os.environ["TBC_API_KEY"],
        os.environ["TBC_CLIENT_ID"],
        os.environ["TBC_CLIENT_SECRET"],
    ) as tbc:
        payment = await tbc.get_payment(payment_id)
    if payment.status == "Succeeded":
        # Store payment.pay_id under a unique database constraint before fulfilment.
        pass
    return Response(status_code=200)
