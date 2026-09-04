"""MCP transport ports and the optional official Streamable HTTP binding."""

from __future__ import annotations

import asyncio
import importlib
import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from typing import Any, Protocol, TypeAlias

from zenture._mcp.contracts import BearerTokenProvider, McpEndpoint
from zenture.errors import ZentureMCPDependencyError, ZentureMCPError

AsyncBearerTokenProvider: TypeAlias = str | Callable[[], str | Awaitable[str]]


class SyncMcpTransport(Protocol):
    """Synchronous protocol port used by the sync adapter and local tests."""

    def list_tools(self) -> object:
        """Return the negotiated MCP tool catalog."""

    def call_tool(self, name: str, arguments: Mapping[str, object]) -> object:
        """Invoke one negotiated MCP tool."""


class AsyncMcpTransport(Protocol):
    """Asynchronous protocol port used by the official transport and tests."""

    async def list_tools(self) -> object:
        """Return the negotiated MCP tool catalog."""

    async def call_tool(self, name: str, arguments: Mapping[str, object]) -> object:
        """Invoke one negotiated MCP tool."""


def resolve_bearer_token(provider: BearerTokenProvider | AsyncBearerTokenProvider) -> str:
    """Resolve one caller value without implementing a token lifecycle."""

    value: object = provider() if callable(provider) else provider
    if inspect.isawaitable(value):
        raise TypeError("async bearer providers require the asynchronous transport")
    return _validate_bearer_value(value)


async def resolve_async_bearer_token(provider: AsyncBearerTokenProvider) -> str:
    """Resolve one asynchronous caller value without refreshing or storing it."""

    value: object = provider() if callable(provider) else provider
    if inspect.isawaitable(value):
        value = await value
    return _validate_bearer_value(value)


def _validate_bearer_value(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 4096:
        raise ValueError("bearer token must be a bounded non-empty value")
    return value


class _OfficialAsyncMcpTransport:
    """Small wrapper around one initialized official MCP client session."""

    def __init__(self, session: Any) -> None:
        self._session = session

    async def list_tools(self) -> object:
        return await self._session.list_tools()

    async def call_tool(self, name: str, arguments: Mapping[str, object]) -> object:
        return await self._session.call_tool(name, arguments=dict(arguments))


@asynccontextmanager
async def open_streamable_http_transport(
    endpoint: str | McpEndpoint,
    *,
    bearer_token: AsyncBearerTokenProvider,
    timeout: float = 30.0,
) -> AsyncGenerator[AsyncMcpTransport, None]:
    """Open an initialized official Streamable HTTP MCP client session.

    The optional ``mcp`` dependency is imported only when this explicit
    integration is opened. The yielded transport retains no credential beyond
    the lifetime managed by the official session.
    """

    target = endpoint if isinstance(endpoint, McpEndpoint) else McpEndpoint.from_value(endpoint)
    if type(timeout) not in {int, float} or timeout <= 0 or timeout > 300:
        raise ValueError("timeout must be between 0 and 300 seconds")
    token = await resolve_async_bearer_token(bearer_token)
    try:
        mcp_module = importlib.import_module("mcp")
        streamable_http_module = importlib.import_module("mcp.client.streamable_http")
        httpx2_module = importlib.import_module("httpx2")
        client_session = mcp_module.ClientSession
        streamablehttp_client = streamable_http_module.streamable_http_client
        async_client = httpx2_module.AsyncClient
        timeout_type = httpx2_module.Timeout
    except (ImportError, AttributeError) as exc:
        raise ZentureMCPDependencyError() from exc

    yielded = False
    body_completed = False
    try:
        async with (
            async_client(
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout_type(timeout, read=timeout),
                follow_redirects=False,
            ) as http_client,
            streamablehttp_client(target.url, http_client=http_client) as streams,
        ):
            read_stream, write_stream = streams
            async with client_session(read_stream, write_stream) as session:
                await session.initialize()
                yielded = True
                yield _OfficialAsyncMcpTransport(session)
                body_completed = True
    except asyncio.CancelledError:
        raise
    except ZentureMCPError:
        raise
    except Exception as exc:
        if yielded and not body_completed:
            raise
        raise ZentureMCPError(
            "mcp_transport_unavailable",
            status_code=503,
            retryable=True,
            next_action="retry_later",
        ) from exc


__all__ = [
    "AsyncBearerTokenProvider",
    "AsyncMcpTransport",
    "SyncMcpTransport",
    "open_streamable_http_transport",
    "resolve_async_bearer_token",
    "resolve_bearer_token",
]
