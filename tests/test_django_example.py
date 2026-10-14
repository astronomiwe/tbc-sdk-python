"""Exercise the documented callback through Django's real middleware stack."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.conf import settings
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import path

from examples.django.payments import views

if not settings.configured:
    settings.configure(DEFAULT_CHARSET="utf-8")


def csrf_failure_view(request, reason=""):
    return HttpResponse(status=403)


def csrf_protected_view(request):
    return HttpResponse(status=200)


urlpatterns = [
    path("webhooks/tbc/", views.tbc_callback),
    path("csrf-protected/", csrf_protected_view),
]


@override_settings(
    ROOT_URLCONF=__name__,
    CSRF_FAILURE_VIEW=__name__ + ".csrf_failure_view",
    MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
    ALLOWED_HOSTS=["testserver"],
)
@pytest.mark.parametrize(
    ("body", "expected_status"),
    [(b'{"PaymentId":"payment-1"}', 200), (b"not-json", 400), (b"{}", 400), (b"[]", 400)],
)
def test_callback_example_with_csrf_middleware(body, expected_status, monkeypatch):
    for name in ("TBC_API_KEY", "TBC_CLIENT_ID", "TBC_CLIENT_SECRET"):
        monkeypatch.setenv(name, "test-only")
    with patch.object(views, "TBCClient") as client_class:
        payment_client = client_class.return_value.__enter__.return_value
        payment_client.get_payment.return_value = SimpleNamespace(status="Succeeded")
        response = Client(enforce_csrf_checks=True).post(
            "/webhooks/tbc/", data=body, content_type="application/json"
        )
    assert response.status_code == expected_status
    if expected_status == 200:
        payment_client.get_payment.assert_called_once_with("payment-1")
    else:
        client_class.assert_not_called()


@override_settings(
    ROOT_URLCONF=__name__,
    CSRF_FAILURE_VIEW=__name__ + ".csrf_failure_view",
    MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
    ALLOWED_HOSTS=["testserver"],
)
def test_middleware_rejects_unexempt_post():
    response = Client(enforce_csrf_checks=True).post("/csrf-protected/")
    assert response.status_code == 403
