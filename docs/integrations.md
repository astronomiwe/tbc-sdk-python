# Framework integrations

The framework extras only parse callback requests. They keep connection lifecycle and
order persistence in your application, where those policies belong.

## FastAPI

```bash
pip install "tbc-payments[fastapi]"
```

```python
from fastapi import FastAPI, Request, Response
from tbc_payments import AsyncTBCClient
from tbc_payments.integrations.fastapi import payment_id_from_request

app = FastAPI()


@app.post("/webhooks/tbc")
async def tbc_callback(request: Request) -> Response:
    payment_id = await payment_id_from_request(request)
    async with AsyncTBCClient("api-key", "client-id", "client-secret") as tbc:
        payment = await tbc.get_payment(payment_id)
    if payment.status == "Succeeded":
        # Atomically mark the order paid using payment.pay_id.
        pass
    return Response(status_code=200)
```

## Django

```bash
pip install "tbc-payments[django]"
```

```python
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
    with TBCClient("api-key", "client-id", "client-secret") as tbc:
        payment = tbc.get_payment(payment_id)
    if payment.status == "Succeeded":
        # Atomically mark the order paid using payment.pay_id.
        pass
    return HttpResponse(status=200)
```

For a class-based view with idempotent fulfilment, see the
[Django class-based callback view](django-callback.md) recipe.
