"""Private helpers shared by resource wrappers."""

from __future__ import annotations

from typing import TypeVar
from urllib.parse import quote

from pydantic import ValidationError

from zenture.errors import ZentureResponseError
from zenture.idempotency import validate_idempotency_key
from zenture.models import SDKBaseModel

ModelT = TypeVar("ModelT", bound=SDKBaseModel)


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
