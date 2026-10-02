from unittest.mock import patch

import httpx
import pytest

from tbc_payments import TBCAPIError, TBCAuthenticationError
from tbc_payments._base import TBCConfig, parse_response, retry_delay, should_retry_status


@pytest.mark.parametrize(
    "kwargs",
    [
        {"api_key": "", "client_id": "id", "client_secret": "secret"},
        {"api_key": "key", "client_id": "id", "client_secret": "secret", "timeout": 0},
        {"api_key": "key", "client_id": "id", "client_secret": "secret", "max_retries": -1},
    ],
)
def test_config_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        TBCConfig(**kwargs)  # type: ignore[arg-type]


def test_parse_response_handles_empty_and_non_json_success() -> None:
    assert parse_response(httpx.Response(204)) == {}
    with pytest.raises(TBCAPIError, match="Expected JSON object"):
        parse_response(httpx.Response(200, json=["unexpected"]))


def test_parse_response_preserves_api_error_details() -> None:
    with pytest.raises(TBCAuthenticationError) as error:
        parse_response(httpx.Response(401, json={"developerMessage": "bad credentials"}))

    assert error.value.status_code == 401
    assert str(error.value) == "bad credentials"


def test_parse_response_handles_non_json_error() -> None:
    with pytest.raises(TBCAPIError, match="gateway unavailable"):
        parse_response(httpx.Response(502, text="gateway unavailable"))


def test_retry_helpers() -> None:
    assert should_retry_status(429)
    assert should_retry_status(500)
    assert not should_retry_status(400)
    with patch("tbc_payments._base.secrets.randbelow", return_value=50):
        assert retry_delay(2) == 1.05
