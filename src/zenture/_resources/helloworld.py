"""Helloworld resource for the public quickstart endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zenture._transport import AsyncTransport, SyncTransport


class HelloworldResource:
    """Synchronous wrapper for `GET /v1/helloworld`."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def get(self) -> str:
        """Return public quickstart markdown."""

        return self._transport.request_text("GET", "/helloworld", auth=False)


class AsyncHelloworldResource:
    """Asynchronous wrapper for `GET /v1/helloworld`."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def get(self) -> str:
        """Return public quickstart markdown."""

        return await self._transport.request_text("GET", "/helloworld", auth=False)
