# Django class-based callback view

A copy-pasteable Django class-based view that receives a TBC callback, confirms the
payment with TBC, and schedules idempotent fulfilment.

```bash
pip install "tbc-payments[django]"
```

## The view

```python
import os

from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from tbc_payments import TBCCallbackError, TBCClient
from tbc_payments.integrations.django import payment_id_from_request

from .models import Order
from .tasks import fulfil_order


@method_decorator(csrf_exempt, name="dispatch")
class TBCCallbackView(View):
    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            payment_id = payment_id_from_request(request)
        except TBCCallbackError:
            return HttpResponseBadRequest()

        # The callback body is not proof of payment: ask TBC for the real status.
        with TBCClient(
            os.environ["TBC_API_KEY"],
            os.environ["TBC_CLIENT_ID"],
            os.environ["TBC_CLIENT_SECRET"],
        ) as tbc:
            payment = tbc.get_payment(payment_id)

        if payment.status == "Succeeded":
            with transaction.atomic():
                # Only the first callback for this payment flips the row.
                marked = Order.objects.filter(
                    tbc_pay_id=payment.pay_id, paid_at__isnull=True
                ).update(paid_at=timezone.now())
                if marked:
                    transaction.on_commit(lambda: fulfil_order.delay(payment.pay_id))

        return HttpResponse(status=200)
```

Route it in your URL configuration:

```python
from django.urls import path

from .views import TBCCallbackView

urlpatterns = [
    path("webhooks/tbc/", TBCCallbackView.as_view()),
]
```

The example assumes an `Order` model that stores the TBC `pay_id` when you create the
payment, and a background task `fulfil_order` (Celery shown; any task queue works):

```python
class Order(models.Model):
    tbc_pay_id = models.CharField(max_length=64, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
```

## How it works

**CSRF exemption.** TBC cannot send a Django CSRF token, so the view is wrapped in
`csrf_exempt`. Without it, `CsrfViewMiddleware` rejects every callback with HTTP 403.
`http_method_names = ["post"]` makes Django answer other methods with HTTP 405.

**Parsing.** `payment_id_from_request` reads the JSON body and returns the `PaymentId`.
It raises `TBCCallbackError` for malformed input, which the view turns into HTTP 400.

**Verification.** The callback only says that something happened to a payment. It is
not signed, so anyone can post one. The view therefore fetches the payment with
`get_payment` and acts only on the status that TBC returns.

**Idempotent fulfilment.** TBC can deliver the same callback more than once, and two
deliveries can arrive at the same time. The conditional `UPDATE ... WHERE paid_at IS
NULL` runs atomically in the database, so exactly one request gets `marked == 1` and
schedules fulfilment. Repeated callbacks update zero rows and do nothing. Keep
`tbc_pay_id` unique so one payment can never match two orders. A task queue may still
retry `fulfil_order`, so make the task itself idempotent as well.

**Prompt HTTP 200.** The view does one TBC lookup and one database update, then returns
HTTP 200. Slow work such as emails or stock changes runs in `fulfil_order`, outside the
request. `transaction.on_commit` schedules that task only after the update is committed,
so a rolled-back transaction never fulfils an order.

**Errors.** If `get_payment` raises a `TBCError` (network failure, TBC outage), the view
lets Django return HTTP 500 so the failure is visible in your logs and monitoring. Do not
mark the order as paid in that case; the payment can still be reconciled later with
`get_payment`.

See [Callbacks and webhooks](callbacks.md) for the callback payload and
[Framework integrations](integrations.md) for the function-based variant.
