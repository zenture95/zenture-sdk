"""HTTPX transport lifecycle primitives."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import httpx
import pytest

from zenture._transport import AsyncTransport, SyncTransport
from zenture.config import ZentureConfig
from zenture.errors import (
    ZentureDependencyUnavailableError,
    ZentureResponseError,
    ZentureTransportError,
    ZentureValidationError,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def test_sync_transport_public_surface_does_not_expose_authorization_header() -> None:
    config = ZentureConfig(api_key="zt_test_transport_123")
    transport = SyncTransport(config=config, user_agent="zenture-test/0")

    assert not hasattr(transport, "default_headers")
    assert "zt_test_transport_123" not in repr(transport)
    assert "Authorization" not in repr(transport)
    assert not transport.is_closed

    transport.close()

    assert transport.is_closed


def test_sync_transport_builds_authorization_only_for_internal_requests() -> None:
    config = ZentureConfig(api_key="zt_test_transport_123")
    transport = SyncTransport(config=config, user_agent="zenture-test/0")
    build_headers = cast(
        "Callable[[], dict[str, str]]",
        object.__getattribute__(transport, "_request_headers"),
    )

    assert build_headers() == {
        "Authorization": "Bearer zt_test_transport_123",
        "User-Agent": "zenture-test/0",
    }

    transport.close()


def test_sync_transport_request_text_can_skip_authorization() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(200, text="hello")

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert transport.request_text("GET", "/helloworld", auth=False) == "hello"
    assert "authorization" not in seen_headers


def test_sync_transport_request_json_sends_headers_and_auth() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(200, json={"ok": True})

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    payload = transport.request_json(
        "POST",
        "/operations",
        headers={"Idempotency-Key": "operation-123"},
        json={"operation_type": "chat"},
    )

    assert payload == {"ok": True}
    assert seen_headers["authorization"] == "Bearer zt_test_transport_123"
    assert seen_headers["idempotency-key"] == "operation-123"


def test_sync_transport_owned_client_uses_explicit_timeout_policy() -> None:
    config = ZentureConfig(
        api_key="zt_test_transport_123",
        connect_timeout=1.0,
        read_timeout=2.0,
        write_timeout=3.0,
        pool_timeout=4.0,
    )
    transport = SyncTransport(config=config)
    client = cast("httpx.Client", object.__getattribute__(transport, "_client"))

    assert client.timeout.connect == 1.0
    assert client.timeout.read == 2.0
    assert client.timeout.write == 3.0
    assert client.timeout.pool == 4.0

    transport.close()


def test_sync_transport_retries_retryable_idempotent_mutation() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                503,
                json={
                    "error": {"code": "dependency_unavailable", "message": "temporary"},
                    "request_id": "req_00000000000000000000000000000000",
                },
            )
        return httpx.Response(200, json={"ok": True})

    transport = SyncTransport(
        config=ZentureConfig(
            api_key="zt_test_transport_123",
            initial_retry_backoff=0.0,
            max_retry_backoff=0.0,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert transport.request_json(
        "POST",
        "/chat",
        headers={"Idempotency-Key": "retry-123"},
    ) == {"ok": True}
    assert attempts == 2


def test_sync_transport_does_not_retry_mutation_without_idempotency_key() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            503,
            json={
                "error": {"code": "dependency_unavailable", "message": "temporary"},
                "request_id": "req_00000000000000000000000000000000",
            },
        )

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureDependencyUnavailableError):
        transport.request_json("POST", "/chat")

    assert attempts == 1


def test_sync_transport_honors_retry_after_header_without_sleeping_when_zero() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={
                    "error": {"code": "rate_limited", "message": "slow down"},
                    "request_id": "req_00000000000000000000000000000000",
                },
            )
        return httpx.Response(200, json={"ok": True})

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert transport.request_json("GET", "/usage") == {"ok": True}
    assert attempts == 2


def test_sync_transport_request_json_rejects_invalid_success_json() -> None:
    token = "zt_" + "live_" + "jsonSECRET"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=f"not-json {token}")

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureResponseError, match="not valid JSON") as exc_info:
        transport.request_json("GET", "/operations/op_123")

    assert token not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


def test_sync_transport_maps_error_response() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {"code": "validation_failed", "message": "invalid"},
                "request_id": "req_00000000000000000000000000000000",
            },
        )

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureValidationError):
        transport.request_text("GET", "/helloworld", auth=False)


def test_sync_transport_rejects_invalid_error_json() -> None:
    token = "zt_" + "live_" + "jsonSECRET"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=f"not-json {token}")

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureResponseError, match="error response was not valid JSON") as exc_info:
        transport.request_text("GET", "/helloworld", auth=False)

    assert token not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


def test_sync_transport_rejects_non_object_error_json() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json=["not", "an", "object"])

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureResponseError, match="error response was not an object"):
        transport.request_text("GET", "/helloworld", auth=False)


def test_sync_transport_redacts_httpx_errors() -> None:
    token = "zt_" + "live_" + "transportSECRET"

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed with token {token}")

    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureTransportError) as exc_info:
        transport.request_text("GET", "/helloworld")

    assert token not in str(exc_info.value)
    assert "<redacted>" in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


def test_sync_transport_context_manager_closes_owned_client() -> None:
    with SyncTransport(config=ZentureConfig(api_key="zt_test_transport_123")) as transport:
        assert not transport.is_closed

    assert transport.is_closed


def test_sync_transport_does_not_close_external_client() -> None:
    client = httpx.Client()
    transport = SyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=client,
    )

    transport.close()

    assert not client.is_closed
    client.close()


@pytest.mark.asyncio
async def test_async_transport_builds_authorization_only_for_internal_requests() -> None:
    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        user_agent="zenture-test/0",
    )
    build_headers = cast(
        "Callable[[], dict[str, str]]",
        object.__getattribute__(transport, "_request_headers"),
    )

    assert build_headers() == {
        "Authorization": "Bearer zt_test_transport_123",
        "User-Agent": "zenture-test/0",
    }

    await transport.aclose()


@pytest.mark.asyncio
async def test_async_transport_request_text_can_skip_authorization() -> None:
    seen_headers: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(200, text="hello")

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    assert await transport.request_text("GET", "/helloworld", auth=False) == "hello"
    assert "authorization" not in seen_headers


@pytest.mark.asyncio
async def test_async_transport_request_json_sends_headers_and_auth() -> None:
    seen_headers: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(200, json={"ok": True})

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    payload = await transport.request_json(
        "POST",
        "/operations",
        headers={"Idempotency-Key": "operation-123"},
        json={"operation_type": "chat"},
    )

    assert payload == {"ok": True}
    assert seen_headers["authorization"] == "Bearer zt_test_transport_123"
    assert seen_headers["idempotency-key"] == "operation-123"


@pytest.mark.asyncio
async def test_async_transport_owned_client_uses_explicit_timeout_policy() -> None:
    config = ZentureConfig(
        api_key="zt_test_transport_123",
        connect_timeout=1.0,
        read_timeout=2.0,
        write_timeout=3.0,
        pool_timeout=4.0,
    )
    transport = AsyncTransport(config=config)
    client = cast("httpx.AsyncClient", object.__getattribute__(transport, "_client"))

    assert client.timeout.connect == 1.0
    assert client.timeout.read == 2.0
    assert client.timeout.write == 3.0
    assert client.timeout.pool == 4.0

    await transport.aclose()


@pytest.mark.asyncio
async def test_async_transport_retries_retryable_idempotent_mutation() -> None:
    attempts = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                503,
                json={
                    "error": {"code": "dependency_unavailable", "message": "temporary"},
                    "request_id": "req_00000000000000000000000000000000",
                },
            )
        return httpx.Response(200, json={"ok": True})

    transport = AsyncTransport(
        config=ZentureConfig(
            api_key="zt_test_transport_123",
            initial_retry_backoff=0.0,
            max_retry_backoff=0.0,
        ),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    assert await transport.request_json(
        "POST",
        "/chat",
        headers={"Idempotency-Key": "retry-123"},
    ) == {"ok": True}
    assert attempts == 2


@pytest.mark.asyncio
async def test_async_transport_does_not_retry_mutation_without_idempotency_key() -> None:
    attempts = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            503,
            json={
                "error": {"code": "dependency_unavailable", "message": "temporary"},
                "request_id": "req_00000000000000000000000000000000",
            },
        )

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureDependencyUnavailableError):
        await transport.request_json("POST", "/chat")

    assert attempts == 1


@pytest.mark.asyncio
async def test_async_transport_request_json_rejects_invalid_success_json() -> None:
    token = "zt_" + "live_" + "jsonSECRET"

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=f"not-json {token}")

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureResponseError, match="not valid JSON") as exc_info:
        await transport.request_json("GET", "/operations/op_123")

    assert token not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


@pytest.mark.asyncio
async def test_async_transport_maps_error_response() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {"code": "validation_failed", "message": "invalid"},
                "request_id": "req_00000000000000000000000000000000",
            },
        )

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureValidationError):
        await transport.request_text("GET", "/helloworld", auth=False)


@pytest.mark.asyncio
async def test_async_transport_rejects_invalid_error_json() -> None:
    token = "zt_" + "live_" + "jsonSECRET"

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=f"not-json {token}")

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureResponseError, match="error response was not valid JSON") as exc_info:
        await transport.request_text("GET", "/helloworld", auth=False)

    assert token not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


@pytest.mark.asyncio
async def test_async_transport_rejects_non_object_error_json() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json=["not", "an", "object"])

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureResponseError, match="error response was not an object"):
        await transport.request_text("GET", "/helloworld", auth=False)


@pytest.mark.asyncio
async def test_async_transport_redacts_httpx_errors() -> None:
    token = "zt_" + "live_" + "transportSECRET"

    async def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed with token {token}")

    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureTransportError) as exc_info:
        await transport.request_text("GET", "/helloworld")

    assert token not in str(exc_info.value)
    assert "<redacted>" in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None


@pytest.mark.asyncio
async def test_async_transport_context_manager_closes_owned_client() -> None:
    async with AsyncTransport(config=ZentureConfig(api_key="zt_test_transport_123")) as transport:
        assert not transport.is_closed

    assert transport.is_closed


@pytest.mark.asyncio
async def test_async_transport_does_not_close_external_client() -> None:
    client = httpx.AsyncClient()
    transport = AsyncTransport(
        config=ZentureConfig(api_key="zt_test_transport_123"),
        client=client,
    )

    await transport.aclose()

    assert not client.is_closed
    await client.aclose()
