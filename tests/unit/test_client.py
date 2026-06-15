"""Public client bootstrap and helloworld resource behavior."""

from __future__ import annotations

import httpx
import pytest

import zenture
from zenture import AsyncZenture, Zenture
from zenture.errors import ZentureAuthenticationError


def test_public_clients_are_exported() -> None:
    assert zenture.__all__ == ("AsyncZenture", "Zenture", "__version__")
    assert zenture.Zenture is Zenture
    assert zenture.AsyncZenture is AsyncZenture


def test_sync_client_repr_redacts_api_key() -> None:
    client = Zenture(api_key="zt_test_client_123")

    assert "zt_test_client_123" not in repr(client)
    assert "<redacted>" in repr(client)
    assert "https://api.zenture.app/v1" in repr(client)

    client.close()


def test_sync_client_accepts_int_base_url() -> None:
    client = Zenture(api_key="zt_test_client_123", base_url="https://api-int.zenture.app")

    assert "https://api-int.zenture.app/v1" in repr(client)

    client.close()


def test_sync_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZENTURE_API_KEY", "zt_test_client_env")
    monkeypatch.setenv("ZENTURE_BASE_URL", "https://api-int.zenture.app")
    client = Zenture.from_env()

    assert "zt_test_client_env" not in repr(client)
    assert "https://api-int.zenture.app/v1" in repr(client)

    client.close()


def test_sync_helloworld_returns_markdown_without_authorization_header() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        assert request.method == "GET"
        assert request.url == "https://api.zenture.app/v1/helloworld"
        return httpx.Response(200, text="# Hello from zenture")

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.helloworld() == "# Hello from zenture"
    assert "authorization" not in seen_headers

    client.close()


def test_sync_client_maps_error_responses_without_leaking_tokens() -> None:
    token = "zt_" + "live_" + "abc123SECRET"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "error": {
                    "code": "unauthorized",
                    "message": f"invalid token {token}",
                },
                "request_id": "req_00000000000000000000000000000000",
            },
        )

    client = Zenture(
        api_key="zt_test_client_123",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureAuthenticationError) as exc_info:
        client.helloworld()

    assert token not in str(exc_info.value)
    assert "<redacted>" in str(exc_info.value)

    client.close()


def test_sync_client_context_manager_closes_owned_client() -> None:
    with Zenture(api_key="zt_test_client_123") as client:
        assert not client.is_closed

    assert client.is_closed


@pytest.mark.asyncio
async def test_async_helloworld_returns_markdown_without_authorization_header() -> None:
    seen_headers: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        assert request.method == "GET"
        assert request.url == "https://api.zenture.app/v1/helloworld"
        return httpx.Response(200, text="# Hello from zenture")

    client = AsyncZenture(
        api_key="zt_test_client_123",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    assert await client.helloworld() == "# Hello from zenture"
    assert "authorization" not in seen_headers

    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_repr_redacts_api_key() -> None:
    client = AsyncZenture(api_key="zt_test_client_123", base_url="https://api-int.zenture.app")

    assert "zt_test_client_123" not in repr(client)
    assert "<redacted>" in repr(client)
    assert "https://api-int.zenture.app/v1" in repr(client)

    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZENTURE_API_KEY", "zt_test_client_env")
    monkeypatch.setenv("ZENTURE_BASE_URL", "https://api-int.zenture.app")
    client = AsyncZenture.from_env()

    assert "zt_test_client_env" not in repr(client)
    assert "https://api-int.zenture.app/v1" in repr(client)

    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_context_manager_closes_owned_client() -> None:
    async with AsyncZenture(api_key="zt_test_client_123") as client:
        assert not client.is_closed

    assert client.is_closed
