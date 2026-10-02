"""Add ``path('webhooks/tbc/', tbc_callback)`` to your Django URL configuration."""

from __future__ import annotations

import os

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from tbc_payments import TBCCallbackError, TBCClient
from tbc_payments.integrations.django import payment_id_from_request


@csrf_exempt
@require_POST
def tbc_callback(request: HttpRequest) -> HttpResponse:
    try:
        payment_id = payment_id_from_request(request)
    except TBCCallbackError:
        return HttpResponseBadRequest()
    with TBCClient(
        os.environ["TBC_API_KEY"],
        os.environ["TBC_CLIENT_ID"],
        os.environ["TBC_CLIENT_SECRET"],
    ) as tbc:
        payment = tbc.get_payment(payment_id)
    if payment.status == "Succeeded":
        # Store payment.pay_id under a unique database constraint before fulfilment.
        pass
    return HttpResponse(status=200)
