"""Minimal sandbox contract check run only by GitHub Actions with configured secrets."""

from __future__ import annotations

import os
from uuid import uuid4

from tbc_payments import Amount, PaymentRequest, TBCClient


def main() -> None:
    request = PaymentRequest(
        amount=Amount("1.00"),
        return_url=os.environ["TBC_SANDBOX_RETURN_URL"],
        merchant_payment_id=f"sdk-contract-{uuid4()}",
    )
    with TBCClient(
        os.environ["TBC_SANDBOX_API_KEY"],
        os.environ["TBC_SANDBOX_CLIENT_ID"],
        os.environ["TBC_SANDBOX_CLIENT_SECRET"],
        sandbox=True,
    ) as client:
        created_payment = client.create_payment(request)
        retrieved_payment = client.get_payment(created_payment.pay_id)
    if retrieved_payment.pay_id != created_payment.pay_id:
        raise RuntimeError("Sandbox payment lookup returned a different payment ID")


if __name__ == "__main__":
    main()
