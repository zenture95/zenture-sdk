"""Operation resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenture._contract import PublicOperationResponse
from zenture._resources._utils import parse_response, path_segment

if TYPE_CHECKING:
    from zenture._transport import AsyncTransport, SyncTransport


class OperationsResource:
    """Synchronous wrapper for operation read routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def get(self, operation_id: str) -> PublicOperationResponse:
        """Fetch one public operation."""

        payload = self._transport.request_json(
            "GET",
            f"/operations/{path_segment(operation_id)}",
        )
        return parse_response(PublicOperationResponse, payload)


class AsyncOperationsResource:
    """Asynchronous wrapper for operation read routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def get(self, operation_id: str) -> PublicOperationResponse:
        """Fetch one public operation."""

        payload = await self._transport.request_json(
            "GET",
            f"/operations/{path_segment(operation_id)}",
        )
        return parse_response(PublicOperationResponse, payload)
