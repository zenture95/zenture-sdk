"""Public client bootstrap and helloworld resource behavior."""

from __future__ import annotations

import httpx
import pytest

import zenture
from zenture import AsyncZenture, Zenture
from zenture.errors import ZentureAuthenticationError

LIVE_CLIENT_KEY = "zt_" + "live_" + "client_123"
TEST_CLIENT_KEY = "zt_" + "test_" + "client_123"
TEST_CLIENT_ENV_KEY = "zt_" + "test_" + "client_env"
NON_PROD_OVERRIDE_ENV = "ZENTURE_SDK_ALLOW_NON_PROD_BASE_URL"
INT_API_BASE_URL = "https://api-int.zenture.app"


def test_public_clients_are_exported() -> None:
    assert zenture.__all__ == ("AsyncZenture", "Zenture", "__version__")
    assert zenture.Zenture is Zenture
    assert zenture.AsyncZenture is AsyncZenture


def test_sync_client_repr_redacts_api_key() -> None:
    client = Zenture(api_key=LIVE_CLIENT_KEY)

    assert LIVE_CLIENT_KEY not in repr(client)
    assert "<redacted>" in repr(client)
    assert "https://api.zenture.app/v1" in repr(client)

    client.close()


def test_sync_client_accepts_non_production_base_url_for_test_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="approved non-production"):
        Zenture(api_key=TEST_CLIENT_KEY, base_url=INT_API_BASE_URL)

    monkeypatch.setenv(NON_PROD_OVERRIDE_ENV, "1")
    client = Zenture(api_key=TEST_CLIENT_KEY, base_url=INT_API_BASE_URL)

    assert f"{INT_API_BASE_URL}/v1" in repr(client)

    client.close()


def test_sync_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZENTURE_API_KEY", TEST_CLIENT_ENV_KEY)
    monkeypatch.setenv("ZENTURE_BASE_URL", INT_API_BASE_URL)
    monkeypatch.setenv(NON_PROD_OVERRIDE_ENV, "1")
    client = Zenture.from_env()

    assert TEST_CLIENT_ENV_KEY not in repr(client)
    assert f"{INT_API_BASE_URL}/v1" in repr(client)

    client.close()


def test_sync_helloworld_returns_markdown_without_authorization_header() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        assert request.method == "GET"
        assert request.url == "https://api.zenture.app/v1/helloworld"
        return httpx.Response(200, text="# Hello from zenture")

    client = Zenture(
        api_key=LIVE_CLIENT_KEY,
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
        api_key=LIVE_CLIENT_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ZentureAuthenticationError) as exc_info:
        client.helloworld()

    assert token not in str(exc_info.value)
    assert "<redacted>" in str(exc_info.value)

    client.close()


def test_sync_client_context_manager_closes_owned_client() -> None:
    with Zenture(api_key=LIVE_CLIENT_KEY) as client:
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
        api_key=LIVE_CLIENT_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    assert await client.helloworld() == "# Hello from zenture"
    assert "authorization" not in seen_headers

    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_repr_redacts_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(NON_PROD_OVERRIDE_ENV, "1")
    client = AsyncZenture(api_key=TEST_CLIENT_KEY, base_url=INT_API_BASE_URL)

    assert TEST_CLIENT_KEY not in repr(client)
    assert "<redacted>" in repr(client)
    assert f"{INT_API_BASE_URL}/v1" in repr(client)

    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZENTURE_API_KEY", TEST_CLIENT_ENV_KEY)
    monkeypatch.setenv("ZENTURE_BASE_URL", INT_API_BASE_URL)
    monkeypatch.setenv(NON_PROD_OVERRIDE_ENV, "1")
    client = AsyncZenture.from_env()

    assert TEST_CLIENT_ENV_KEY not in repr(client)
    assert f"{INT_API_BASE_URL}/v1" in repr(client)

    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_context_manager_closes_owned_client() -> None:
    async with AsyncZenture(api_key=LIVE_CLIENT_KEY) as client:
        assert not client.is_closed

    assert client.is_closed
