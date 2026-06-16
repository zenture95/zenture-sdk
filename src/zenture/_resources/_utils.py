"""Private helpers shared by resource wrappers."""

from __future__ import annotations

from typing import TypeVar
from urllib.parse import quote

from pydantic import ValidationError

from zenture._contract import OperationRunResult, PublicOperationResponse
from zenture.errors import (
    ZenturePollingStoppedError,
    ZenturePollingTimeoutError,
    ZentureResponseError,
)
from zenture.idempotency import validate_idempotency_key
from zenture.models import SDKBaseModel

ModelT = TypeVar("ModelT", bound=SDKBaseModel)
DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 100
MAX_CURSOR_LENGTH = 200


def parse_response(model_type: type[ModelT], payload: object) -> ModelT:
    """Validate a public API response against an SDK contract model."""

    response_error: ZentureResponseError | None = None
    try:
        return model_type.model_validate(payload)
    except ValidationError:
        response_error = ZentureResponseError(
            "Public API response did not match the expected schema."
        )
    raise response_error


def idempotency_headers(idempotency_key: str) -> dict[str, str]:
    """Build idempotency headers after SDK-side safety validation."""

    return {"Idempotency-Key": validate_idempotency_key(idempotency_key)}


def path_segment(value: str) -> str:
    """URL-encode one public API path segment."""

    return quote(value, safe="")


def pagination_params(
    *, limit: int = DEFAULT_PAGE_LIMIT, cursor: str | None = None
) -> dict[str, str]:
    """Validate and build public pagination query parameters."""

    if type(limit) is not int:
        raise ValueError("limit must be an integer.")
    if limit < 1 or limit > MAX_PAGE_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_PAGE_LIMIT}.")
    params = {"limit": str(limit)}

    if cursor is None:
        return params
    if type(cursor) is not str:
        raise ValueError("cursor must be a string.")
    if not cursor or len(cursor) > MAX_CURSOR_LENGTH:
        raise ValueError(f"cursor must be between 1 and {MAX_CURSOR_LENGTH} characters.")
    params["cursor"] = cursor
    return params


def operation_run_result(
    *,
    operation: PublicOperationResponse,
    idempotency_key: str,
) -> OperationRunResult:
    """Build the public run-helper result wrapper."""

    return OperationRunResult(
        operation_id=operation.operation_id,
        status=operation.status,
        result=operation.result,
        error=operation.error,
        idempotency_key=idempotency_key,
        last_request_id=None,
    )


def polling_error_with_context(
    error: ZenturePollingTimeoutError | ZenturePollingStoppedError,
    *,
    operation_id: str,
    idempotency_key: str,
) -> ZenturePollingTimeoutError | ZenturePollingStoppedError:
    """Attach recovery metadata to a local polling error."""

    error.operation_id = operation_id
    error.idempotency_key = idempotency_key
    return error
