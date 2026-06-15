"""Typed exceptions for zenture API responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ValidationError

from zenture.models import ForwardCompatibleErrorEnvelope
from zenture.redaction import redact_text

if TYPE_CHECKING:
    from collections.abc import Mapping


class ZentureError(Exception):
    """Base class for all zenture SDK errors."""


class ZentureAPIError(ZentureError):
    """Base class for public API error responses."""

    def __init__(
        self,
        *,
        message: str,
        error_code: str,
        status_code: int,
        request_id: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.message = redact_text(message)
        self.error_code = error_code
        self.status_code = status_code
        self.request_id = request_id
        self.retry_after = retry_after
        super().__init__(self.message)

    def __str__(self) -> str:
        details = f"{self.status_code} {self.error_code}: {self.message}"
        if self.request_id is not None:
            return f"{details} (request_id={self.request_id})"
        return details

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"status_code={self.status_code!r}, "
            f"request_id={self.request_id!r}, "
            f"retry_after={self.retry_after!r})"
        )


class ZentureAuthenticationError(ZentureAPIError):
    """Raised when an API token is missing, invalid, expired, or revoked."""


class ZenturePermissionError(ZentureAPIError):
    """Raised when the API token lacks the required scope."""


class ZentureValidationError(ZentureAPIError):
    """Raised when request validation fails."""


class ZentureMissingIdempotencyKeyError(ZentureAPIError):
    """Raised when a mutating operation is missing Idempotency-Key."""


class ZentureIdempotencyConflictError(ZentureAPIError):
    """Raised when an idempotency key is reused with a different request."""


class ZentureRateLimitError(ZentureAPIError):
    """Raised when the public API rate limit is exceeded."""


class ZentureCapacityError(ZentureAPIError):
    """Raised when zenture capacity is temporarily unavailable."""


class ZentureDependencyUnavailableError(ZentureAPIError):
    """Raised when a required zenture backend dependency is unavailable."""


class ZentureInternalServerError(ZentureAPIError):
    """Raised for sanitized internal API errors."""


class ZentureOperationExpiredError(ZentureAPIError):
    """Raised when operation polling TTL has expired."""


class ZentureTransportError(ZentureError):
    """Raised for client-side network and timeout failures."""


class ZentureResponseError(ZentureError):
    """Raised when a response cannot be parsed as the public contract."""

    def __init__(self, message: str) -> None:
        self.message = redact_text(message)
        super().__init__(self.message)


_ERROR_TYPES: dict[str, type[ZentureAPIError]] = {
    "unauthorized": ZentureAuthenticationError,
    "forbidden": ZenturePermissionError,
    "validation_failed": ZentureValidationError,
    "missing_idempotency_key": ZentureMissingIdempotencyKeyError,
    "idempotency_conflict": ZentureIdempotencyConflictError,
    "rate_limited": ZentureRateLimitError,
    "capacity_unavailable": ZentureCapacityError,
    "dependency_unavailable": ZentureDependencyUnavailableError,
    "internal_error": ZentureInternalServerError,
    "operation_expired": ZentureOperationExpiredError,
}


def error_from_response(
    *,
    status_code: int,
    payload: Mapping[str, object],
    headers: Mapping[str, str],
) -> ZentureAPIError:
    """Build a typed API error from a public API error envelope."""

    envelope: ForwardCompatibleErrorEnvelope | None = None
    response_error: ZentureResponseError | None = None
    try:
        envelope = ForwardCompatibleErrorEnvelope.model_validate(payload)
    except ValidationError:
        response_error = ZentureResponseError(
            "Public API error envelope did not match the expected schema."
        )
    if response_error is not None:
        raise response_error
    assert envelope is not None

    error_code = envelope.error.code
    message = envelope.error.message
    retry_after = _parse_retry_after(headers.get("Retry-After"))
    error_type = _ERROR_TYPES.get(error_code, ZentureAPIError)
    return error_type(
        message=message,
        error_code=error_code,
        status_code=status_code,
        request_id=envelope.request_id,
        retry_after=retry_after,
    )


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        retry_after = float(value)
    except ValueError:
        return None

    if retry_after < 0:
        return None
    return retry_after
