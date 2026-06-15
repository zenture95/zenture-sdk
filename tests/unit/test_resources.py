"""Resource client behavior for the zenture Public API surface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest

from zenture import AsyncZenture, Zenture
from zenture._contract import OperationStatus, PublicOperationResponse
from zenture.errors import ZentureResponseError

if TYPE_CHECKING:
    from collections.abc import Callable


OPERATION_PAYLOAD = {
    "operation_id": "op_abc123",
    "status": "queued",
    "result": None,
}
CHAT_SUMMARY = {
    "chat_id": "chat_abc123",
    "created_at": "2026-06-15T10:00:00Z",
    "title": "Demo",
    "updated_at": None,
}
CHAT_TURN = {
    "turn_id": "turn_abc123",
    "created_at": "2026-06-15T10:01:00Z",
    "user_message": "Hello",
    "model_answer": "Hi",
}
EVALUATION = {
    "evaluation_id": "eval_abc123",
    "status": "succeeded",
    "score": 0.91,
    "created_at": "2026-06-15T10:02:00Z",
}
PUBLIC_MODEL = {
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


def _create_chat(client: Zenture) -> PublicOperationResponse:
    return client.chat.create_operation(
        message="Hello",
        idempotency_key="chat-create-1",
        chat_id="chat_abc123",
    )


def _create_input_wizard(client: Zenture) -> PublicOperationResponse:
    return client.input_wizard.create(
        prompt="Improve this",
        idempotency_key="wizard-create-1",
    )


def _create_evaluation(client: Zenture) -> PublicOperationResponse:
    return client.evaluations.create(
        user_message="Question",
        ai_answer="Answer",
        idempotency_key="evaluation-create-1",
        chat_id="chat_abc123",
        model_response_id="model_response_123",
        turn_id="turn_abc123",
    )


def test_sync_operation_get_validates_contract_model() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=OPERATION_PAYLOAD)

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    operation = client.operations.get("op_abc123")

    assert operation.operation_id == "op_abc123"
    assert operation.status is OperationStatus.QUEUED
    assert seen[0].method == "GET"
    assert str(seen[0].url) == "https://api.zenture.app/v1/operations/op_abc123"
    assert seen[0].headers["authorization"] == "Bearer zt_test_client_123"

    client.close()


def test_sync_operation_get_returns_failed_operation_with_domain_error_code() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "operation_id": "op_abc123",
                "status": "failed",
                "error": {
                    "code": "chat_execution_failed",
                    "message": "Chat execution failed.",
                },
            },
        )

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    operation = client.operations.get("op_abc123")

    assert operation.status is OperationStatus.FAILED
    assert operation.error is not None
    assert operation.error.code == "chat_execution_failed"
    assert operation.error.message == "Chat execution failed."

    client.close()


def test_sync_resource_response_validation_does_not_chain_raw_payload() -> None:
    token = "zt_" + "live_" + "responseSECRET"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": token})

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureResponseError) as exc_info:
        client.operations.get("op_abc123")

    assert token not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None

    client.close()


@pytest.mark.parametrize(
    ("call", "path", "payload"),
    [
        (
            _create_chat,
            "/v1/chat",
            {"message": "Hello", "chat_id": "chat_abc123", "mode": "single"},
        ),
        (
            _create_input_wizard,
            "/v1/input-wizard",
            {"mode": "prompt_improvement", "prompt": "Improve this"},
        ),
        (
            _create_evaluation,
            "/v1/evaluate",
            {
                "user_message": "Question",
                "ai_answer": "Answer",
                "chat_id": "chat_abc123",
                "model_response_id": "model_response_123",
                "turn_id": "turn_abc123",
            },
        ),
    ],
)
def test_sync_mutating_resources_send_idempotency_and_validate_operation(
    call: Callable[[Zenture], PublicOperationResponse],
    path: str,
    payload: dict[str, str],
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(202, json=OPERATION_PAYLOAD)

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    operation = call(client)

    assert operation.operation_id == "op_abc123"
    assert seen[0].method == "POST"
    assert seen[0].url.path == path
    assert seen[0].headers["authorization"] == "Bearer zt_test_client_123"
    assert seen[0].headers["idempotency-key"]
    assert seen[0].read() == httpx.Request("POST", "https://api.zenture.app", json=payload).read()

    client.close()


def test_sync_chat_read_resources_validate_contract_models() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/chats":
            return httpx.Response(200, json={"chats": [CHAT_SUMMARY], "next_cursor": "cursor_2"})
        if request.url.path == "/v1/chats/chat_abc123":
            return httpx.Response(200, json={"chat": CHAT_SUMMARY, "latest_turns": [CHAT_TURN]})
        if request.url.path == "/v1/chats/chat_abc123/messages":
            return httpx.Response(
                200,
                json={"chat_id": "chat_abc123", "turns": [CHAT_TURN], "next_cursor": None},
            )
        return httpx.Response(404, json={"error": {"code": "not_found", "message": "not found"}})

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    chats = client.chat.list()
    chat = client.chat.get("chat_abc123")
    messages = client.chat.messages("chat_abc123")

    assert chats.chats[0].chat_id == "chat_abc123"
    assert chats.next_cursor == "cursor_2"
    assert chat.latest_turns[0].turn_id == "turn_abc123"
    assert messages.turns[0].model_answer == "Hi"

    client.close()


def test_sync_models_resource_lists_models_with_optional_mode_filter() -> None:
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"models": [PUBLIC_MODEL]})

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    all_models = client.models.list()
    multi_models = client.models.list(mode="multi")

    assert all_models.models[0].id == "model-public-1"
    assert multi_models.models[0].modes[1].value == "multi"
    assert seen_urls == [
        "https://api.zenture.app/v1/models",
        "https://api.zenture.app/v1/models?mode=multi",
    ]

    client.close()


def test_sync_chat_create_operation_validates_single_and_multi_model_modes() -> None:
    seen_json: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_json.append(request.read())
        return httpx.Response(202, json=OPERATION_PAYLOAD)

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    single = client.chat.create_operation(
        message="Hello",
        idempotency_key="chat-single-1",
        mode="single",
        model="model-public-1",
    )
    multi = client.chat.create_operation(
        message="Hello",
        idempotency_key="chat-multi-1",
        mode="multi",
        models=["model-public-1", "model-public-2"],
    )

    assert single.operation_id == "op_abc123"
    assert multi.operation_id == "op_abc123"
    assert (
        seen_json[0]
        == httpx.Request(
            "POST",
            "https://api.zenture.app",
            json={"message": "Hello", "mode": "single", "model": "model-public-1"},
        ).read()
    )
    assert (
        seen_json[1]
        == httpx.Request(
            "POST",
            "https://api.zenture.app",
            json={
                "message": "Hello",
                "mode": "multi",
                "models": ["model-public-1", "model-public-2"],
            },
        ).read()
    )

    client.close()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "single", "models": ["model-public-1"]},
        {"mode": "multi"},
        {"mode": "multi", "model": "model-public-1", "models": ["model-public-2"]},
        {"mode": "multi", "models": ["model-public-1", "model-public-1"]},
        {"mode": "multi", "models": ["model-1", "model-2", "model-3", "model-4"]},
        {"mode": "agentic"},
    ],
)
def test_sync_chat_create_operation_rejects_invalid_model_mode_combinations(
    kwargs: dict[str, Any],
) -> None:
    client = Zenture(api_key="zt_test_client_123")

    with pytest.raises(ValueError, match=r"single|multi|models|Input should|agentic"):
        client.chat.create_operation(
            message="Hello",
            idempotency_key="invalid-chat-mode",
            **kwargs,
        )

    client.close()


def test_sync_chat_run_polls_operation_and_returns_idempotency_metadata() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/v1/chat":
            return httpx.Response(202, json=OPERATION_PAYLOAD)
        return httpx.Response(
            200,
            json={
                "operation_id": "op_abc123",
                "status": "succeeded",
                "result": {
                    "result_type": "chat",
                    "chat_id": "chat_abc123",
                    "status": "succeeded",
                },
            },
        )

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.chat.run(
        message="Hello",
        mode="multi",
        models=["model-public-1", "model-public-2"],
        idempotency_key="chat-run-1",
        poll_interval=0.01,
        timeout=1.0,
    )

    assert result.operation_id == "op_abc123"
    assert result.status is OperationStatus.SUCCEEDED
    assert result.idempotency_key == "chat-run-1"
    assert result.result is not None
    assert result.result.chat_id == "chat_abc123"
    assert seen_paths == ["/v1/chat", "/v1/operations/op_abc123"]

    client.close()


def test_sync_chat_run_returns_terminal_operation_error_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/chat":
            return httpx.Response(202, json=OPERATION_PAYLOAD)
        return httpx.Response(
            200,
            json={
                "operation_id": "op_abc123",
                "status": "failed",
                "error": {
                    "code": "chat_execution_failed",
                    "message": "Chat execution failed.",
                },
            },
        )

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.chat.run(
        message="Hello",
        idempotency_key="chat-run-failed-1",
        poll_interval=0.01,
        timeout=1.0,
    )

    assert result.status is OperationStatus.FAILED
    assert result.error is not None
    assert result.error.code == "chat_execution_failed"
    assert result.error.message == "Chat execution failed."

    client.close()


def test_sync_evaluation_and_account_read_resources_validate_contract_models() -> None:
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        if request.url.path == "/v1/evaluations":
            return httpx.Response(200, json={"evaluations": [EVALUATION], "next_cursor": None})
        if request.url.path == "/v1/evaluations/eval_abc123":
            return httpx.Response(200, json=EVALUATION)
        if request.url.path == "/v1/billing":
            return httpx.Response(200, json={"plan": "pro", "status": "active"})
        if request.url.path == "/v1/usage":
            return httpx.Response(200, json={"scope": "all", "operation_count": 7})
        if request.url.path == "/v1/limits":
            return httpx.Response(
                200,
                json={
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
                },
            )
        return httpx.Response(404, json={"error": {"code": "not_found", "message": "not found"}})

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    evaluations = client.evaluations.list()
    evaluation = client.evaluations.get("eval_abc123")
    billing = client.billing.get()
    usage = client.usage.get(scope="all")
    limits = client.limits.get()

    assert evaluations.evaluations[0].evaluation_id == "eval_abc123"
    assert evaluation.score == 0.91
    assert billing.plan == "pro"
    assert usage.operation_count == 7
    assert limits.routes["POST /v1/chat"].idempotency_required is True
    assert "https://api.zenture.app/v1/usage?scope=all" in seen_urls

    client.close()


@pytest.mark.asyncio
async def test_async_resources_match_sync_surface() -> None:
    seen_paths: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/v1/chat":
            return httpx.Response(202, json=OPERATION_PAYLOAD)
        if request.url.path == "/v1/operations/op_abc123":
            return httpx.Response(
                200,
                json={
                    "operation_id": "op_abc123",
                    "status": "succeeded",
                    "result": {"result_type": "chat", "chat_id": "chat_abc123"},
                },
            )
        if request.url.path == "/v1/evaluations":
            return httpx.Response(200, json={"evaluations": [EVALUATION], "next_cursor": None})
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"models": [PUBLIC_MODEL]})
        return httpx.Response(200, json={"scope": "api", "operation_count": 1})

    client = AsyncZenture(
        api_key="zt_test_client_123",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    created = await client.chat.create_operation(
        message="Hello",
        idempotency_key="async-chat-create",
    )
    run = await client.chat.run(
        message="Hello",
        mode="multi",
        models=["model-public-1", "model-public-2"],
        idempotency_key="async-chat-run",
        poll_interval=0.01,
        timeout=1.0,
    )
    operation = await client.operations.get("op_abc123")
    evaluations = await client.evaluations.list()
    models = await client.models.list(mode="single")
    usage = await client.usage.get()

    assert created.status is OperationStatus.QUEUED
    assert run.status is OperationStatus.SUCCEEDED
    assert operation.operation_id == "op_abc123"
    assert evaluations.evaluations[0].status == "succeeded"
    assert models.models[0].id == "model-public-1"
    assert usage.scope == "api"
    assert seen_paths == [
        "/v1/chat",
        "/v1/chat",
        "/v1/operations/op_abc123",
        "/v1/operations/op_abc123",
        "/v1/evaluations",
        "/v1/models",
        "/v1/usage",
    ]

    await client.aclose()


@pytest.mark.asyncio
async def test_async_chat_run_returns_terminal_operation_error_details() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/chat":
            return httpx.Response(202, json=OPERATION_PAYLOAD)
        return httpx.Response(
            200,
            json={
                "operation_id": "op_abc123",
                "status": "failed",
                "error": {
                    "code": "evaluation_execution_failed",
                    "message": "Evaluation execution failed.",
                },
            },
        )

    client = AsyncZenture(
        api_key="zt_test_client_123",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    result = await client.chat.run(
        message="Hello",
        idempotency_key="async-chat-run-failed",
        poll_interval=0.01,
        timeout=1.0,
    )

    assert result.status is OperationStatus.FAILED
    assert result.error is not None
    assert result.error.code == "evaluation_execution_failed"
    assert result.error.message == "Evaluation execution failed."

    await client.aclose()


def test_api_token_management_surface_is_not_exposed() -> None:
    client = Zenture(api_key="zt_test_client_123")

    assert not hasattr(client, "api_tokens")
    assert not hasattr(client, "tokens")

    client.close()
