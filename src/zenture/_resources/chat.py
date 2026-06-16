"""Chat resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from zenture._contract import (
    ChatRequest,
    ModelMode,
    OperationRunResult,
    PublicChatCollectionResponse,
    PublicChatMessagesResponse,
    PublicChatResponse,
    PublicChatSummary,
    PublicChatTurn,
    PublicOperationResponse,
)
from zenture._resources._utils import (
    idempotency_headers,
    operation_run_result,
    pagination_params,
    parse_response,
    path_segment,
    polling_error_with_context,
)
from zenture._resources.operations import AsyncOperationsResource, OperationsResource
from zenture.errors import ZenturePollingStoppedError, ZenturePollingTimeoutError
from zenture.idempotency import idempotency_key as build_idempotency_key

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from zenture._transport import AsyncTransport, SyncTransport


def _generated_chat_idempotency_key() -> str:
    return build_idempotency_key("chat", uuid4().hex)


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


def _initial_interval(
    *,
    initial_interval: float | None,
    poll_interval: float | None,
) -> float:
    if initial_interval is not None:
        return initial_interval
    if poll_interval is not None:
        return poll_interval
    return 1.0


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
        initial_interval: float | None = None,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
        poll_interval: float | None = None,
    ) -> OperationRunResult:
        """Create and poll a chat operation until it reaches a terminal status."""

        key = idempotency_key or _generated_chat_idempotency_key()
        operation = self.create_operation(
            message=message,
            idempotency_key=key,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )
        try:
            final_operation = OperationsResource(self._transport).wait(
                operation.operation_id,
                timeout=timeout,
                initial_interval=_initial_interval(
                    initial_interval=initial_interval,
                    poll_interval=poll_interval,
                ),
                max_interval=max_interval,
                stop=stop,
            )
        except (ZenturePollingTimeoutError, ZenturePollingStoppedError) as exc:
            raise polling_error_with_context(
                exc,
                operation_id=operation.operation_id,
                idempotency_key=key,
            ) from None
        return operation_run_result(operation=final_operation, idempotency_key=key)

    def list(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PublicChatCollectionResponse:
        """List public chats available to the API token."""

        payload = self._transport.request_json(
            "GET",
            "/chats",
            params=pagination_params(limit=limit, cursor=cursor),
        )
        return parse_response(PublicChatCollectionResponse, payload)

    def iter(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> Iterator[PublicChatSummary]:
        """Iterate public chat summaries until the API returns no next cursor."""

        next_cursor = cursor
        while True:
            page = self.list(limit=limit, cursor=next_cursor)
            yield from page.chats
            if page.next_cursor is None:
                return
            next_cursor = page.next_cursor

    def get(self, chat_id: str) -> PublicChatResponse:
        """Fetch one public chat summary."""

        payload = self._transport.request_json("GET", f"/chats/{path_segment(chat_id)}")
        return parse_response(PublicChatResponse, payload)

    def messages(
        self,
        chat_id: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PublicChatMessagesResponse:
        """Fetch public chat turns."""

        payload = self._transport.request_json(
            "GET",
            f"/chats/{path_segment(chat_id)}/messages",
            params=pagination_params(limit=limit, cursor=cursor),
        )
        return parse_response(PublicChatMessagesResponse, payload)

    def iter_messages(
        self,
        chat_id: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> Iterator[PublicChatTurn]:
        """Iterate public chat turns until the API returns no next cursor."""

        next_cursor = cursor
        while True:
            page = self.messages(chat_id, limit=limit, cursor=next_cursor)
            yield from page.turns
            if page.next_cursor is None:
                return
            next_cursor = page.next_cursor


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
        initial_interval: float | None = None,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
        poll_interval: float | None = None,
    ) -> OperationRunResult:
        """Create and poll a chat operation until it reaches a terminal status."""

        key = idempotency_key or _generated_chat_idempotency_key()
        operation = await self.create_operation(
            message=message,
            idempotency_key=key,
            chat_id=chat_id,
            mode=mode,
            model=model,
            models=models,
        )
        try:
            final_operation = await AsyncOperationsResource(self._transport).wait(
                operation.operation_id,
                timeout=timeout,
                initial_interval=_initial_interval(
                    initial_interval=initial_interval,
                    poll_interval=poll_interval,
                ),
                max_interval=max_interval,
                stop=stop,
            )
        except (ZenturePollingTimeoutError, ZenturePollingStoppedError) as exc:
            raise polling_error_with_context(
                exc,
                operation_id=operation.operation_id,
                idempotency_key=key,
            ) from None
        return operation_run_result(operation=final_operation, idempotency_key=key)

    async def list(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PublicChatCollectionResponse:
        """List public chats available to the API token."""

        payload = await self._transport.request_json(
            "GET",
            "/chats",
            params=pagination_params(limit=limit, cursor=cursor),
        )
        return parse_response(PublicChatCollectionResponse, payload)

    async def iter(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> AsyncIterator[PublicChatSummary]:
        """Iterate public chat summaries until the API returns no next cursor."""

        next_cursor = cursor
        while True:
            page = await self.list(limit=limit, cursor=next_cursor)
            for chat in page.chats:
                yield chat
            if page.next_cursor is None:
                return
            next_cursor = page.next_cursor

    async def get(self, chat_id: str) -> PublicChatResponse:
        """Fetch one public chat summary."""

        payload = await self._transport.request_json("GET", f"/chats/{path_segment(chat_id)}")
        return parse_response(PublicChatResponse, payload)

    async def messages(
        self,
        chat_id: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PublicChatMessagesResponse:
        """Fetch public chat turns."""

        payload = await self._transport.request_json(
            "GET",
            f"/chats/{path_segment(chat_id)}/messages",
            params=pagination_params(limit=limit, cursor=cursor),
        )
        return parse_response(PublicChatMessagesResponse, payload)

    async def iter_messages(
        self,
        chat_id: str,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> AsyncIterator[PublicChatTurn]:
        """Iterate public chat turns until the API returns no next cursor."""

        next_cursor = cursor
        while True:
            page = await self.messages(chat_id, limit=limit, cursor=next_cursor)
            for turn in page.turns:
                yield turn
            if page.next_cursor is None:
                return
            next_cursor = page.next_cursor
