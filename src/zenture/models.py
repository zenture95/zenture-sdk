"""Shared Pydantic models for SDK-internal public API data."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SDKBaseModel(BaseModel):
    """Strict, immutable base model for SDK value objects."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ForwardCompatibleError(SDKBaseModel):
    """Forward-compatible public API error object."""

    code: str
    message: str


class ForwardCompatibleErrorEnvelope(SDKBaseModel):
    """Forward-compatible public API error envelope.

    This intentionally accepts unknown future error codes so the SDK can preserve
    them as `ZentureAPIError` instead of treating a valid future response as a
    contract mismatch.
    """

    error: ForwardCompatibleError
    request_id: str | None = None


class RateLimitInfo(SDKBaseModel):
    """Parsed rate-limit and retry metadata."""

    limit: int | None = None
    remaining: int | None = None
    reset_after: float | None = None
    retry_after: float | None = None
