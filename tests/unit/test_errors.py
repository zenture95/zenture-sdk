"""Typed API error behavior."""

from __future__ import annotations

import pytest

import zenture.models as sdk_models
from zenture.errors import (
    ZentureAPIError,
    ZentureInsufficientCreditsError,
    ZentureMissingIdempotencyKeyError,
    ZentureResponseError,
    error_from_response,
)
from zenture.redaction import REDACTED


def test_error_string_redacts_sensitive_message_content() -> None:
    token = "zt_" + "live_" + "abc123SECRET"

    error = ZentureAPIError(
        message=f"token {token} failed",
        error_code="internal_error",
        status_code=500,
        request_id="req_00000000000000000000000000000000",
    )

    assert token not in str(error)
    assert token not in repr(error)
    assert REDACTED in str(error)
    assert error.request_id == "req_00000000000000000000000000000000"


def test_error_from_response_maps_missing_idempotency_key() -> None:
    error = error_from_response(
        status_code=400,
        payload={
            "error": {
                "code": "missing_idempotency_key",
                "message": "Missing Idempotency-Key",
            },
            "request_id": "req_00000000000000000000000000000001",
        },
        headers={"Retry-After": "3"},
    )

    assert isinstance(error, ZentureMissingIdempotencyKeyError)
    assert error.status_code == 400
    assert error.error_code == "missing_idempotency_key"
    assert error.request_id == "req_00000000000000000000000000000001"
    assert error.retry_after == 3.0


def test_error_from_response_maps_insufficient_credits() -> None:
    error = error_from_response(
        status_code=402,
        payload={
            "error": {
                "code": "insufficient_credits",
                "message": "At least 20.00 credits are required to run this operation.",
            },
            "request_id": "req_00000000000000000000000000000004",
        },
        headers={},
    )

    assert isinstance(error, ZentureInsufficientCreditsError)
    assert error.status_code == 402
    assert error.error_code == "insufficient_credits"


def test_error_from_response_preserves_unknown_error_code_as_base_api_error() -> None:
    token = "zt_" + "live_" + "abc123SECRET"

    error = error_from_response(
        status_code=418,
        payload={
            "error": {
                "code": "new_future_code",
                "message": f"Future error with token {token}",
            },
            "request_id": "req_00000000000000000000000000000002",
        },
        headers={},
    )

    assert type(error) is ZentureAPIError
    assert error.error_code == "new_future_code"
    assert token not in str(error)
    assert token not in repr(error)
    assert REDACTED in str(error)


def test_tolerant_error_envelope_model_is_not_named_like_strict_contract_model() -> None:
    assert not hasattr(sdk_models, "PublicError")
    assert not hasattr(sdk_models, "PublicErrorEnvelope")
    assert hasattr(sdk_models, "ForwardCompatibleError")
    assert hasattr(sdk_models, "ForwardCompatibleErrorEnvelope")


def test_error_from_response_rejects_malformed_error_envelope() -> None:
    token = "zt_" + "live_" + "abc123SECRET"

    with pytest.raises(ZentureResponseError) as exc_info:
        error_from_response(
            status_code=500,
            payload={
                "error": {
                    "code": "internal_error",
                    "message": f"secret {token}",
                    "unexpected": "field",
                },
                "request_id": "req_00000000000000000000000000000003",
            },
            headers={},
        )

    error_message = str(exc_info.value)
    assert token not in error_message
    assert "expected schema" in error_message
    assert "secret" not in error_message
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None
