"""Internal contract model behavior and OpenAPI drift checks."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import BaseModel, ValidationError

import zenture

OPENAPI_PATH = (
    Path(__file__).resolve().parents[3] / "openapi" / "zenture-public-api-v1.openapi.json"
)


def _schemas() -> dict[str, Any]:
    raw_contract = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw_contract, dict)
    contract = cast("dict[str, Any]", raw_contract)
    components = contract["components"]
    assert isinstance(components, dict)
    typed_components = cast("dict[str, Any]", components)
    schemas = typed_components["schemas"]
    assert isinstance(schemas, dict)
    return cast("dict[str, Any]", schemas)


def _contract() -> dict[str, Any]:
    contract = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    assert isinstance(contract, dict)
    return cast("dict[str, Any]", contract)


def test_contract_models_are_internal_not_top_level_exports() -> None:
    assert "PublicOperationResponse" not in zenture.__all__
    assert "ChatRequest" not in zenture.__all__


def test_contract_enums_match_openapi_exactly() -> None:
    from zenture._contract import ModelMode, OperationStatus, PublicErrorCode

    schemas = _schemas()
    operation_status = schemas["OperationStatus"]
    public_error_code = schemas["PublicErrorCode"]
    assert isinstance(operation_status, dict)
    assert isinstance(public_error_code, dict)

    assert [status.value for status in OperationStatus] == operation_status["enum"]
    assert [code.value for code in PublicErrorCode] == public_error_code["enum"]
    assert PublicErrorCode.MISSING_IDEMPOTENCY_KEY.value == "missing_idempotency_key"
    assert [mode.value for mode in ModelMode] == schemas["ModelMode"]["enum"]
    assert schemas["ChatRequest"]["properties"]["mode"]["allOf"] == [
        {"$ref": "#/components/schemas/ModelMode"}
    ]
    assert "agentic" not in {mode.value for mode in ModelMode}


def test_public_operation_result_is_bounded_and_strict() -> None:
    from zenture._contract import OperationStatus, PublicOperationResult

    schema = PublicOperationResult.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["result_type"]

    result = PublicOperationResult(
        result_type="chat",
        chat_id="chat_abc123",
        status=OperationStatus.SUCCEEDED,
    )

    assert isinstance(result, BaseModel)
    assert result.result_type == "chat"

    from_json = PublicOperationResult.model_validate(
        {
            "result_type": "chat",
            "chat_id": "chat_abc123",
            "completed_at": "2026-06-15T12:00:00Z",
            "status": "succeeded",
        }
    )
    assert from_json.status is OperationStatus.SUCCEEDED
    assert from_json.completed_at == datetime(2026, 6, 15, 12, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        PublicOperationResult.model_validate({"result_type": "chat", "unexpected": True})
    with pytest.raises(ValidationError):
        PublicOperationResult.model_validate({"result_type": "chat", "completed_at": "not-a-date"})


def test_public_operation_response_matches_contract_shape() -> None:
    from zenture._contract import (
        OperationStatus,
        PublicOperationError,
        PublicOperationResponse,
        PublicOperationResult,
    )

    response = PublicOperationResponse(
        operation_id="op_abc123",
        status=OperationStatus.SUCCEEDED,
        result=PublicOperationResult(result_type="evaluation", evaluation_id="eval_abc123"),
    )

    assert response.operation_id == "op_abc123"
    assert response.result is not None

    from_json = PublicOperationResponse.model_validate(
        {"operation_id": "op_abc123", "status": "queued"}
    )
    assert from_json.status is OperationStatus.QUEUED

    failed = PublicOperationResponse.model_validate(
        {
            "operation_id": "op_abc123",
            "status": "failed",
            "error": {
                "code": "chat_execution_failed",
                "message": "Chat execution failed.",
            },
        }
    )
    assert failed.status is OperationStatus.FAILED
    assert isinstance(failed.error, PublicOperationError)
    assert failed.error.code == "chat_execution_failed"

    with pytest.raises(ValidationError):
        PublicOperationResponse(operation_id="bad", status=OperationStatus.QUEUED)


def test_public_error_envelope_requires_known_error_code_and_request_id() -> None:
    from zenture._contract import PublicError, PublicErrorCode, PublicErrorEnvelope

    envelope = PublicErrorEnvelope(
        error=PublicError(
            code=PublicErrorCode.MISSING_IDEMPOTENCY_KEY,
            message="Public gateway error",
        ),
        request_id="req_00000000000000000000000000000000",
    )

    assert envelope.error.code is PublicErrorCode.MISSING_IDEMPOTENCY_KEY
    from_json = PublicErrorEnvelope.model_validate(
        {
            "error": {"code": "validation_failed", "message": "x"},
            "request_id": "req_00000000000000000000000000000000",
        }
    )
    assert from_json.error.code is PublicErrorCode.VALIDATION_FAILED

    with pytest.raises(ValidationError):
        PublicErrorEnvelope.model_validate(
            {"error": {"code": PublicErrorCode.VALIDATION_FAILED, "message": "x"}}
        )
    with pytest.raises(ValidationError):
        PublicError.model_validate({"code": "unknown_code", "message": "x"})


def test_mutation_request_models_are_strict_and_match_required_fields() -> None:
    from zenture._contract import ChatRequest, EvaluateRequest, InputWizardRequest, ModelMode

    assert ChatRequest(message="hello").message == "hello"
    assert ChatRequest(message="hello").mode is ModelMode.SINGLE
    assert ChatRequest(message="hello", mode=ModelMode.SINGLE, model="default-model").model == (
        "default-model"
    )
    assert ChatRequest.model_validate(
        {"message": "hello", "mode": "multi", "models": ["model-a", "model-b"]}
    ).models == ("model-a", "model-b")
    assert EvaluateRequest(user_message="question", ai_answer="answer").ai_answer == "answer"
    assert InputWizardRequest(mode="prompt_improvement", prompt="make this better").mode == (
        "prompt_improvement"
    )

    with pytest.raises(ValidationError):
        ChatRequest(message="")
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"message": "hello", "extra_field": True})
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"message": "hello", "mode": "single", "models": ["model-a"]})
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"message": "hello", "mode": "multi"})
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {
                "message": "hello",
                "mode": "multi",
                "model": "model-a",
                "models": ["model-b"],
            }
        )
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {"message": "hello", "mode": "multi", "models": ["model-a", "model-a"]}
        )
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"message": "hello", "mode": "multi", "models": [""]})
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"message": "hello", "mode": "multi", "models": ["m" * 141]})
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"message": "hello", "mode": "agentic"})
    with pytest.raises(ValidationError):
        EvaluateRequest.model_validate({"user_message": "question"})
    with pytest.raises(ValidationError):
        InputWizardRequest.model_validate({"mode": "other", "prompt": "x"})


def test_mutation_request_models_required_fields_match_openapi() -> None:
    from zenture._contract import ChatRequest, EvaluateRequest, InputWizardRequest

    schemas = _schemas()

    assert ChatRequest.model_json_schema()["required"] == schemas["ChatRequest"]["required"]
    assert EvaluateRequest.model_json_schema()["required"] == schemas["EvaluateRequest"]["required"]
    assert (
        InputWizardRequest.model_json_schema()["required"]
        == schemas["InputWizardRequest"]["required"]
    )


def test_phase_four_response_models_match_required_fields() -> None:
    from zenture._contract import (
        LimitsResponse,
        PublicBillingResponse,
        PublicChatCollectionResponse,
        PublicChatMessagesResponse,
        PublicChatResponse,
        PublicEvaluationCollectionResponse,
        PublicEvaluationResponse,
        PublicModelListResponse,
        PublicUsageResponse,
    )

    schemas = _schemas()

    model_pairs: dict[str, type[BaseModel]] = {
        "LimitsResponse": LimitsResponse,
        "PublicModelListResponse": PublicModelListResponse,
        "PublicBillingResponse": PublicBillingResponse,
        "PublicChatCollectionResponse": PublicChatCollectionResponse,
        "PublicChatMessagesResponse": PublicChatMessagesResponse,
        "PublicChatResponse": PublicChatResponse,
        "PublicEvaluationCollectionResponse": PublicEvaluationCollectionResponse,
        "PublicEvaluationResponse": PublicEvaluationResponse,
        "PublicUsageResponse": PublicUsageResponse,
    }

    for schema_name, model_type in model_pairs.items():
        assert model_type.model_json_schema()["additionalProperties"] is False
        assert model_type.model_json_schema()["required"] == schemas[schema_name]["required"]


def test_phase_four_response_models_validate_api_json() -> None:
    from zenture._contract import (
        LimitsResponse,
        ModelMode,
        PublicBillingResponse,
        PublicChatCollectionResponse,
        PublicEvaluationCollectionResponse,
        PublicModelListResponse,
        PublicUsageResponse,
    )

    models = PublicModelListResponse.model_validate(
        {
            "models": [
                {
                    "id": "model-public-1",
                    "display_name": "General model",
                    "modes": ["single", "multi"],
                    "capabilities": ["chat"],
                    "is_default": True,
                    "is_available": True,
                    "cost_class": "standard",
                    "provider_display_name": None,
                    "max_input_tokens": 16000,
                }
            ]
        }
    )
    chat_collection = PublicChatCollectionResponse.model_validate(
        {
            "chats": [
                {
                    "chat_id": "chat_abc123",
                    "created_at": "2026-06-15T10:00:00Z",
                    "title": None,
                }
            ],
            "next_cursor": None,
        }
    )
    evaluation_collection = PublicEvaluationCollectionResponse.model_validate(
        {"evaluations": [{"evaluation_id": "eval_abc123", "status": "queued"}]}
    )
    billing = PublicBillingResponse.model_validate({"plan": "pro", "status": "active"})
    usage = PublicUsageResponse.model_validate({"scope": "api", "operation_count": 3})
    limits = LimitsResponse.model_validate(
        {
            "routes": {
                "POST /v1/chat": {
                    "auth_mode": "api_token",
                    "scopes": ["chat:create"],
                    "cost_class": "expensive",
                    "idempotency_required": True,
                    "cors_policy": "server_only",
                    "max_body_bytes": 65536,
                    "rate_limit_per_minute": 10,
                }
            },
            "operation_statuses": ["queued", "running", "succeeded"],
        }
    )

    assert models.models[0].modes == (ModelMode.SINGLE, ModelMode.MULTI)
    assert chat_collection.chats[0].chat_id == "chat_abc123"
    assert evaluation_collection.evaluations[0].evaluation_id == "eval_abc123"
    assert billing.plan == "pro"
    assert usage.operation_count == 3
    assert limits.routes["POST /v1/chat"].scopes == ("chat:create",)

    with pytest.raises(ValidationError):
        PublicModelListResponse.model_validate(
            {
                "models": [
                    {
                        "id": "model-public-1",
                        "display_name": "General model",
                        "modes": ["single"],
                        "capabilities": [""],
                        "is_default": True,
                        "is_available": True,
                        "cost_class": "standard",
                    }
                ]
            }
        )
    with pytest.raises(ValidationError):
        PublicModelListResponse.model_validate(
            {
                "models": [
                    {
                        "id": "model-public-1",
                        "display_name": "General model",
                        "modes": ["single"],
                        "capabilities": ["c" * 41],
                        "is_default": True,
                        "is_available": True,
                        "cost_class": "standard",
                    }
                ]
            }
        )


def test_phase_four_collection_models_are_deeply_immutable() -> None:
    from zenture._contract import LimitsResponse, PublicChatCollectionResponse

    chat_collection = PublicChatCollectionResponse.model_validate(
        {
            "chats": [
                {
                    "chat_id": "chat_abc123",
                    "created_at": "2026-06-15T10:00:00Z",
                }
            ]
        }
    )
    limits = LimitsResponse.model_validate(
        {
            "routes": {
                "POST /v1/chat": {
                    "auth_mode": "api_token",
                    "scopes": ["chat:create"],
                    "cost_class": "expensive",
                    "idempotency_required": True,
                    "cors_policy": "server_only",
                    "max_body_bytes": 65536,
                    "rate_limit_per_minute": 10,
                }
            },
            "operation_statuses": ["queued"],
        }
    )

    assert chat_collection.chats == (chat_collection.chats[0],)
    assert limits.operation_statuses == ("queued",)
    assert limits.routes["POST /v1/chat"].scopes == ("chat:create",)


def test_rate_limit_header_helpers_match_openapi_headers() -> None:
    from zenture._contract import RATE_LIMIT_HEADER_NAMES, RateLimitInfo, parse_rate_limit_headers

    contract = _contract()
    components = contract["components"]
    assert isinstance(components, dict)
    typed_components = cast("dict[str, Any]", components)
    headers = typed_components["headers"]
    assert isinstance(headers, dict)
    typed_headers = cast("dict[str, Any]", headers)

    assert set(RATE_LIMIT_HEADER_NAMES) == {
        "RateLimit-Limit",
        "RateLimit-Remaining",
        "RateLimit-Reset",
        "Retry-After",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    }
    assert set(typed_headers) == {
        "RateLimitLimit",
        "RateLimitRemaining",
        "RateLimitReset",
        "RetryAfter",
        "XRateLimitLimit",
        "XRateLimitRemaining",
        "XRateLimitReset",
    }
    assert parse_rate_limit_headers({"RateLimit-Limit": "10"}) == RateLimitInfo(limit=10)


def test_contract_surface_excludes_api_token_management_models() -> None:
    import zenture._contract as contract

    exported_names = set(contract.__all__)

    assert "ApiToken" not in "".join(exported_names)
    assert "API_TOKEN_MANAGEMENT_PATHS" not in exported_names
