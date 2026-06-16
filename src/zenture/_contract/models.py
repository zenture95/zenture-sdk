"""Internal contract models derived from the zenture Public API OpenAPI artifact."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self, cast

from pydantic import AwareDatetime, Field, field_validator, model_validator

from zenture.models import SDKBaseModel


class OperationStatus(StrEnum):
    """Public operation lifecycle statuses."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PublicErrorCode(StrEnum):
    """Stable public API error codes."""

    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    RATE_LIMITED = "rate_limited"
    VALIDATION_FAILED = "validation_failed"
    MISSING_IDEMPOTENCY_KEY = "missing_idempotency_key"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    CAPACITY_UNAVAILABLE = "capacity_unavailable"
    INTERNAL_ERROR = "internal_error"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    OPERATION_EXPIRED = "operation_expired"


class ModelMode(StrEnum):
    """Public chat model execution modes."""

    SINGLE = "single"
    MULTI = "multi"


PublicOperationResultType = Literal["input_wizard", "chat", "evaluation", "unknown"]
ModelCostClass = Literal["economy", "standard", "premium", "frontier"]
ModelCapability = Annotated[str, Field(min_length=1, max_length=40)]
ModelId = Annotated[str, Field(min_length=1, max_length=140)]
UsageScope = Literal["api", "all"]


def _coerce_aware_datetime(value: object) -> object:
    if not isinstance(value, str):
        return value

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware.")
    return parsed


def _coerce_tuple(value: object) -> object:
    if isinstance(value, list):
        return tuple(cast("list[object]", value))
    return value


class PublicError(SDKBaseModel):
    """Public API error object with a bounded stable code."""

    code: PublicErrorCode
    message: str = Field(min_length=1)

    @field_validator("code", mode="before")
    @classmethod
    def _coerce_code(cls, value: object) -> object:
        if isinstance(value, str):
            return PublicErrorCode(value)
        return value


class PublicErrorEnvelope(SDKBaseModel):
    """Public API error envelope."""

    error: PublicError
    request_id: str = Field(pattern=r"^req_[a-f0-9]{32}$")


class PublicOperationResult(SDKBaseModel):
    """Bounded safe-reference operation result."""

    result_type: PublicOperationResultType
    chat_id: str | None = Field(default=None, pattern=r"^chat_[A-Za-z0-9_-]{3,128}$")
    completed_at: AwareDatetime | None = None
    evaluation_id: str | None = Field(default=None, pattern=r"^eval_[A-Za-z0-9_-]{3,128}$")
    model_response_id: str | None = Field(default=None, max_length=140)
    resource_id: str | None = None
    status: OperationStatus | None = None
    turn_id: str | None = Field(default=None, max_length=140)

    @field_validator("completed_at", mode="before")
    @classmethod
    def _coerce_completed_at(cls, value: object) -> object:
        return _coerce_aware_datetime(value)

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, value: object) -> object:
        if isinstance(value, str):
            return OperationStatus(value)
        return value


class PublicOperationError(SDKBaseModel):
    """Terminal operation error with domain-specific operation code."""

    code: str
    message: str


class PublicOperationResponse(SDKBaseModel):
    """Operation response returned by mutating async routes."""

    operation_id: str = Field(pattern=r"^op_[A-Za-z0-9_-]{3,128}$")
    status: OperationStatus
    result: PublicOperationResult | None = None
    error: PublicOperationError | None = None

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, value: object) -> object:
        if isinstance(value, str):
            return OperationStatus(value)
        return value


class PublicChatSummary(SDKBaseModel):
    """Public chat summary returned by chat read routes."""

    chat_id: str = Field(pattern=r"^chat_[A-Za-z0-9_-]{3,128}$")
    created_at: AwareDatetime | None
    title: str | None = None
    updated_at: AwareDatetime | None = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_datetimes(cls, value: object) -> object:
        return _coerce_aware_datetime(value)


class PublicChatTurn(SDKBaseModel):
    """Public chat turn returned by message routes."""

    turn_id: str
    created_at: AwareDatetime | None
    user_message: str
    model_answer: str

    @field_validator("created_at", mode="before")
    @classmethod
    def _coerce_created_at(cls, value: object) -> object:
        return _coerce_aware_datetime(value)


def _empty_chat_turns() -> tuple[PublicChatTurn, ...]:
    return ()


class PublicChatCollectionResponse(SDKBaseModel):
    """Public chat list response."""

    chats: tuple[PublicChatSummary, ...]
    next_cursor: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("chats", mode="before")
    @classmethod
    def _coerce_chats(cls, value: object) -> object:
        return _coerce_tuple(value)


class PublicChatResponse(SDKBaseModel):
    """Public chat detail response."""

    chat: PublicChatSummary
    latest_turns: tuple[PublicChatTurn, ...] = Field(default_factory=_empty_chat_turns)

    @field_validator("latest_turns", mode="before")
    @classmethod
    def _coerce_latest_turns(cls, value: object) -> object:
        return _coerce_tuple(value)


class PublicChatMessagesResponse(SDKBaseModel):
    """Public chat messages response."""

    chat_id: str = Field(pattern=r"^chat_[A-Za-z0-9_-]{3,128}$")
    turns: tuple[PublicChatTurn, ...]
    next_cursor: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("turns", mode="before")
    @classmethod
    def _coerce_turns(cls, value: object) -> object:
        return _coerce_tuple(value)


class PublicEvaluationResponse(SDKBaseModel):
    """Public evaluation detail response."""

    evaluation_id: str = Field(pattern=r"^eval_[A-Za-z0-9_-]{3,128}$")
    status: str
    score: float | None = None
    created_at: AwareDatetime | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def _coerce_created_at(cls, value: object) -> object:
        return _coerce_aware_datetime(value)


class PublicEvaluationCollectionResponse(SDKBaseModel):
    """Public evaluation list response."""

    evaluations: tuple[PublicEvaluationResponse, ...]
    next_cursor: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("evaluations", mode="before")
    @classmethod
    def _coerce_evaluations(cls, value: object) -> object:
        return _coerce_tuple(value)


class PublicBillingResponse(SDKBaseModel):
    """Public billing status response."""

    plan: str
    status: str
    current_period_end: AwareDatetime | None = None

    @field_validator("current_period_end", mode="before")
    @classmethod
    def _coerce_current_period_end(cls, value: object) -> object:
        return _coerce_aware_datetime(value)


class PublicUsageResponse(SDKBaseModel):
    """Public usage response."""

    scope: UsageScope
    operation_count: int = Field(ge=0)


class RouteLimitProjection(SDKBaseModel):
    """Public per-route limits projection."""

    auth_mode: str
    scopes: tuple[str, ...]
    cost_class: str
    idempotency_required: bool
    cors_policy: str
    max_body_bytes: int
    rate_limit_per_minute: int

    @field_validator("scopes", mode="before")
    @classmethod
    def _coerce_scopes(cls, value: object) -> object:
        return _coerce_tuple(value)


class LimitsResponse(SDKBaseModel):
    """Public limits response."""

    routes: dict[str, RouteLimitProjection]
    operation_statuses: tuple[str, ...]

    @field_validator("operation_statuses", mode="before")
    @classmethod
    def _coerce_operation_statuses(cls, value: object) -> object:
        return _coerce_tuple(value)


class PublicModel(SDKBaseModel):
    """Public model descriptor returned by model discovery."""

    id: ModelId
    display_name: str = Field(min_length=1, max_length=120)
    modes: tuple[ModelMode, ...] = Field(min_length=1, max_length=2)
    capabilities: tuple[ModelCapability, ...] = Field(max_length=12)
    is_default: bool
    is_available: bool
    cost_class: ModelCostClass
    provider_display_name: str | None = Field(default=None, min_length=1, max_length=80)
    max_input_tokens: int | None = Field(default=None, ge=1)

    @field_validator("modes", mode="before")
    @classmethod
    def _coerce_modes(cls, value: object) -> object:
        if isinstance(value, list):
            return tuple(ModelMode(item) for item in cast("list[str]", value))
        return value

    @field_validator("capabilities", mode="before")
    @classmethod
    def _coerce_capabilities(cls, value: object) -> object:
        return _coerce_tuple(value)


class PublicModelListResponse(SDKBaseModel):
    """Public model discovery response."""

    models: tuple[PublicModel, ...]

    @field_validator("models", mode="before")
    @classmethod
    def _coerce_models(cls, value: object) -> object:
        return _coerce_tuple(value)


class ChatRequest(SDKBaseModel):
    """Request body for `POST /v1/chat`."""

    message: str = Field(min_length=1, max_length=20000)
    chat_id: str | None = Field(default=None, min_length=8, max_length=140)
    mode: ModelMode = ModelMode.SINGLE
    model: ModelId | None = None
    models: tuple[ModelId, ...] | None = Field(default=None, min_length=1, max_length=3)

    @field_validator("mode", mode="before")
    @classmethod
    def _coerce_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return ModelMode(value)
        return value

    @field_validator("models", mode="before")
    @classmethod
    def _coerce_models(cls, value: object) -> object:
        return _coerce_tuple(value)

    @model_validator(mode="after")
    def _validate_model_mode(self) -> Self:
        if self.models is not None and len(set(self.models)) != len(self.models):
            raise ValueError("models must be unique.")
        if self.mode is ModelMode.SINGLE:
            if self.models is not None:
                raise ValueError("single mode does not accept models.")
            return self
        if self.model is not None:
            raise ValueError("multi mode does not accept model.")
        if self.models is None:
            raise ValueError("multi mode requires models.")
        return self


class OperationRunResult(SDKBaseModel):
    """SDK operation run wrapper returned by high-level polling helpers."""

    operation_id: str = Field(pattern=r"^op_[A-Za-z0-9_-]{3,128}$")
    status: OperationStatus
    result: PublicOperationResult | None = None
    error: PublicOperationError | None = None
    idempotency_key: str = Field(min_length=1, max_length=255)
    last_request_id: str | None = None


class EvaluateRequest(SDKBaseModel):
    """Request body for `POST /v1/evaluate`."""

    user_message: str = Field(min_length=1, max_length=40000)
    ai_answer: str = Field(min_length=1, max_length=40000)
    chat_id: str | None = Field(default=None, min_length=8, max_length=140)
    model_response_id: str | None = Field(default=None, min_length=1, max_length=140)
    turn_id: str | None = Field(default=None, min_length=1, max_length=140)


class InputWizardRequest(SDKBaseModel):
    """Request body for `POST /v1/input-wizard`."""

    mode: Literal["prompt_improvement"]
    prompt: str = Field(min_length=1, max_length=20000)
