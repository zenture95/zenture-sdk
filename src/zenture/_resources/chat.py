"""Chat resource wrappers."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING
from uuid import uuid4

from zenture._contract import (
    ChatRequest,
    ModelMode,
    OperationRunResult,
    PublicChatCollectionResponse,
    PublicChatMessagesResponse,
    PublicChatResponse,
    PublicOperationResponse,
)
from zenture._resources._utils import idempotency_headers, parse_response, path_segment
from zenture.idempotency import idempotency_key as build_idempotency_key
from zenture.polling import is_terminal_status

if TYPE_CHECKING:
    from zenture._transport import AsyncTransport, SyncTransport


def _generated_chat_idempotency_key() -> str:
    return build_idempotency_key("chat", uuid4().hex)


def _validate_polling(timeout: float, poll_interval: float) -> None:
    if timeout <= 0:
        raise ValueError("timeout must be positive.")
    if poll_interval <= 0:
        raise ValueError("poll_interval must be positive.")


def _chat_request(
    *,
    message: str,
    chat_id: str | None,
    mode: ModelMode | str,
    model: str | None,
    models: list[str] | tuple[str, ...] | None,
) -> ChatRequest:
    models_tuple = None if models is None else tuple(models)
    return ChatRequest(
        message=message,
        chat_id=chat_id,
        mode=ModelMode(mode),
        model=model,
        models=models_tuple,
    )


class ChatResource:
    """Synchronous wrapper for chat routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        message: str,
        idempotency_key: str,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous chat operation."""

        return self.create_operation(
            message=message,
            idempotency_key=idempotency_key,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )

    def create_operation(
        self,
        *,
        message: str,
        idempotency_key: str,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous chat operation."""

        body = _chat_request(
            message=message,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )
        payload = self._transport.request_json(
            "POST",
            "/chat",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(exclude_none=True),
        )
        return parse_response(PublicOperationResponse, payload)

    def run(
        self,
        *,
        message: str,
        idempotency_key: str | None = None,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
        timeout: float = 120.0,
        poll_interval: float = 1.0,
    ) -> OperationRunResult:
        """Create and poll a chat operation until it reaches a terminal status."""

        _validate_polling(timeout, poll_interval)
        key = idempotency_key or _generated_chat_idempotency_key()
        operation = self.create_operation(
            message=message,
            idempotency_key=key,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )
        deadline = time.monotonic() + timeout
        while not is_terminal_status(operation.status):
            if time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting for chat operation to finish.")
            time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
            payload = self._transport.request_json(
                "GET",
                f"/operations/{path_segment(operation.operation_id)}",
            )
            operation = parse_response(PublicOperationResponse, payload)

        return OperationRunResult(
            operation_id=operation.operation_id,
            status=operation.status,
            result=operation.result,
            error=operation.error,
            idempotency_key=key,
        )

    def list(self) -> PublicChatCollectionResponse:
        """List public chats available to the API token."""

        payload = self._transport.request_json("GET", "/chats")
        return parse_response(PublicChatCollectionResponse, payload)

    def get(self, chat_id: str) -> PublicChatResponse:
        """Fetch one public chat summary."""

        payload = self._transport.request_json("GET", f"/chats/{path_segment(chat_id)}")
        return parse_response(PublicChatResponse, payload)

    def messages(self, chat_id: str) -> PublicChatMessagesResponse:
        """Fetch public chat turns."""

        payload = self._transport.request_json(
            "GET",
            f"/chats/{path_segment(chat_id)}/messages",
        )
        return parse_response(PublicChatMessagesResponse, payload)


class AsyncChatResource:
    """Asynchronous wrapper for chat routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        message: str,
        idempotency_key: str,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous chat operation."""

        return await self.create_operation(
            message=message,
            idempotency_key=idempotency_key,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )

    async def create_operation(
        self,
        *,
        message: str,
        idempotency_key: str,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous chat operation."""

        body = _chat_request(
            message=message,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )
        payload = await self._transport.request_json(
            "POST",
            "/chat",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(exclude_none=True),
        )
        return parse_response(PublicOperationResponse, payload)

    async def run(
        self,
        *,
        message: str,
        idempotency_key: str | None = None,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
        timeout: float = 120.0,
        poll_interval: float = 1.0,
    ) -> OperationRunResult:
        """Create and poll a chat operation until it reaches a terminal status."""

        _validate_polling(timeout, poll_interval)
        key = idempotency_key or _generated_chat_idempotency_key()
        operation = await self.create_operation(
            message=message,
            idempotency_key=key,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )
        deadline = time.monotonic() + timeout
        while not is_terminal_status(operation.status):
            if time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting for chat operation to finish.")
            await asyncio.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
            payload = await self._transport.request_json(
                "GET",
                f"/operations/{path_segment(operation.operation_id)}",
            )
            operation = parse_response(PublicOperationResponse, payload)

        return OperationRunResult(
            operation_id=operation.operation_id,
            status=operation.status,
            result=operation.result,
            error=operation.error,
            idempotency_key=key,
        )

    async def list(self) -> PublicChatCollectionResponse:
        """List public chats available to the API token."""

        payload = await self._transport.request_json("GET", "/chats")
        return parse_response(PublicChatCollectionResponse, payload)

    async def get(self, chat_id: str) -> PublicChatResponse:
        """Fetch one public chat summary."""

        payload = await self._transport.request_json("GET", f"/chats/{path_segment(chat_id)}")
        return parse_response(PublicChatResponse, payload)

    async def messages(self, chat_id: str) -> PublicChatMessagesResponse:
        """Fetch public chat turns."""

        payload = await self._transport.request_json(
            "GET",
            f"/chats/{path_segment(chat_id)}/messages",
        )
        return parse_response(PublicChatMessagesResponse, payload)
