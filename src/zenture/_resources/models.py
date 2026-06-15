"""Model discovery resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenture._contract import ModelMode, PublicModelListResponse
from zenture._resources._utils import parse_response

if TYPE_CHECKING:
    from zenture._transport import AsyncTransport, SyncTransport


def _model_mode_value(mode: ModelMode | str | None) -> str | None:
    if mode is None:
        return None
    return ModelMode(mode).value


class ModelsResource:
    """Synchronous wrapper for model discovery routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self, *, mode: ModelMode | str | None = None) -> PublicModelListResponse:
        """List public models available to the API token."""

        mode_value = _model_mode_value(mode)
        params = None if mode_value is None else {"mode": mode_value}
        payload = self._transport.request_json("GET", "/models", params=params)
        return parse_response(PublicModelListResponse, payload)


class AsyncModelsResource:
    """Asynchronous wrapper for model discovery routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self, *, mode: ModelMode | str | None = None) -> PublicModelListResponse:
        """List public models available to the API token."""

        mode_value = _model_mode_value(mode)
        params = None if mode_value is None else {"mode": mode_value}
        payload = await self._transport.request_json("GET", "/models", params=params)
        return parse_response(PublicModelListResponse, payload)
