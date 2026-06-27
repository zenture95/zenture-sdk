"""Chat resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenture._contract import (
    ChatRequest,
)
from zenture._resources._utils import (
    idempotency_headers,
    next_page_cursor,
    operation_run_result,
    pagination_params,
    parse_response,
    path_segment,
    polling_error_with_context,
)
from zenture._resources.operations import AsyncOperationsResource, OperationsResource
from zenture.errors import ZenturePollingStoppedError, ZenturePollingTimeoutError
from zenture.types import (
    ModelMode,
    OperationRunResult,
    PublicChatCollectionResponse,
    PublicChatMessagesResponse,
    PublicChatResponse,
    PublicChatSummary,
    PublicChatTurn,
    PublicOperationResponse,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from zenture._transport import AsyncTransport, SyncTransport


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


def _turn_by_id(turns: tuple[PublicChatTurn, ...], turn_id: str | None) -> PublicChatTurn | None:
    if turn_id is None:
        return None
    return next((turn for turn in turns if turn.turn_id == turn_id), None)


class ChatResource:
    """Synchronous wrapper for chat routes.

    Start a new chat by omitting ``chat_id``. Continue an existing chat by
    passing the returned ``chat_id``. A completed chat operation exposes safe ids
    on ``OperationRunResult.result`` including ``chat_id``, ``turn_id``, and
    ``model_response_id``/``model_response_ids``. Use those response ids when
    evaluating a zenture chat answer with ``client.evaluations``.
    """

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
        """Create an asynchronous chat operation.

        ``idempotency_key`` is caller-owned and required. Reuse it only for a
        retry of the same request body. Pass ``chat_id`` to append a follow-up
        turn to an existing chat.
        """

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
        """Create an asynchronous chat operation.

        The operation result will later contain safe chat references when
        polling succeeds. For single-model chats, use the returned
        ``model_response_id`` as the AI-answer id for internal evaluation.
        """

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
        idempotency_key: str,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
        timeout: float = 120.0,
        initial_interval: float | None = None,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
        poll_interval: float | None = None,
        include_content: bool = False,
    ) -> OperationRunResult:
        """Create and poll a chat operation until it reaches a terminal status.

        The returned ``result`` contains the ``chat_id`` for follow-up turns and
        the ``turn_id`` plus ``model_response_id``/``model_response_ids`` for
        evaluating the generated answer. Set ``include_content=True`` to attach
        the matching public chat turn as ``chat_turn`` after the operation
        succeeds. ``idempotency_key`` must be stable for the logical chat turn;
        reuse it only when retrying the same request body.
        """

        operation = self.create_operation(
            message=message,
            idempotency_key=idempotency_key,
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
                idempotency_key=idempotency_key,
            ) from None
        run_result = operation_run_result(
            operation=final_operation,
            idempotency_key=idempotency_key,
        )
        if (
            not include_content
            or run_result.result is None
            or run_result.result.chat_id is None
            or run_result.result.turn_id is None
        ):
            return run_result
        messages = self.messages(run_result.result.chat_id)
        return run_result.model_copy(
            update={"chat_turn": _turn_by_id(messages.turns, run_result.result.turn_id)}
        )

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
        seen_cursors: set[str] = set() if cursor is None else {cursor}
        while True:
            page = self.list(limit=limit, cursor=next_cursor)
            yield from page.chats
            returned_cursor = next_page_cursor(
                seen_cursors=seen_cursors,
                returned_cursor=page.next_cursor,
            )
            if returned_cursor is None:
                return
            seen_cursors.add(returned_cursor)
            next_cursor = returned_cursor

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
        """Fetch public chat turns.

        Each turn includes ``user_message``, ``model_answer``, and the safe
        ``model_response_id``/``model_response_ids`` needed to evaluate an
        existing zenture chat answer.
        """

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
        seen_cursors: set[str] = set() if cursor is None else {cursor}
        while True:
            page = self.messages(chat_id, limit=limit, cursor=next_cursor)
            yield from page.turns
            returned_cursor = next_page_cursor(
                seen_cursors=seen_cursors,
                returned_cursor=page.next_cursor,
            )
            if returned_cursor is None:
                return
            seen_cursors.add(returned_cursor)
            next_cursor = returned_cursor


class AsyncChatResource:
    """Asynchronous wrapper for chat routes.

    Start a new chat by omitting ``chat_id`` and continue a chat by passing the
    returned ``chat_id``. Completed chat operations and chat message reads expose
    ``model_response_id``/``model_response_ids`` for evaluating zenture chat
    answers.
    """

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
        """Create an asynchronous chat operation.

        ``idempotency_key`` is caller-owned and required. Pass ``chat_id`` to
        append a follow-up turn to an existing chat.
        """

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
        """Create an asynchronous chat operation.

        Poll this operation to receive safe chat references. For single-model
        chats, the terminal result includes the AI-answer ``model_response_id``
        used by internal evaluation.
        """

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
        idempotency_key: str,
        chat_id: str | None = None,
        mode: ModelMode | str = ModelMode.SINGLE,
        model: str | None = None,
        models: list[str] | tuple[str, ...] | None = None,
        timeout: float = 120.0,
        initial_interval: float | None = None,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
        poll_interval: float | None = None,
        include_content: bool = False,
    ) -> OperationRunResult:
        """Create and poll a chat operation until it reaches a terminal status.

        The returned ``result`` contains ``chat_id`` for follow-up turns and
        ``turn_id`` plus ``model_response_id``/``model_response_ids`` for
        evaluating the generated answer. ``idempotency_key`` must be stable for
        the logical chat turn.
        """

        operation = await self.create_operation(
            message=message,
            idempotency_key=idempotency_key,
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
                idempotency_key=idempotency_key,
            ) from None
        run_result = operation_run_result(
            operation=final_operation,
            idempotency_key=idempotency_key,
        )
        if (
            not include_content
            or run_result.result is None
            or run_result.result.chat_id is None
            or run_result.result.turn_id is None
        ):
            return run_result
        messages = await self.messages(run_result.result.chat_id)
        return run_result.model_copy(
            update={"chat_turn": _turn_by_id(messages.turns, run_result.result.turn_id)}
        )

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
        seen_cursors: set[str] = set() if cursor is None else {cursor}
        while True:
            page = await self.list(limit=limit, cursor=next_cursor)
            for chat in page.chats:
                yield chat
            returned_cursor = next_page_cursor(
                seen_cursors=seen_cursors,
                returned_cursor=page.next_cursor,
            )
            if returned_cursor is None:
                return
            seen_cursors.add(returned_cursor)
            next_cursor = returned_cursor

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
        """Fetch public chat turns.

        Each turn includes ``user_message``, ``model_answer``, and the safe
        ``model_response_id``/``model_response_ids`` needed to evaluate an
        existing zenture chat answer.
        """

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
        seen_cursors: set[str] = set() if cursor is None else {cursor}
        while True:
            page = await self.messages(chat_id, limit=limit, cursor=next_cursor)
            for turn in page.turns:
                yield turn
            returned_cursor = next_page_cursor(
                seen_cursors=seen_cursors,
                returned_cursor=page.next_cursor,
            )
            if returned_cursor is None:
                return
            seen_cursors.add(returned_cursor)
            next_cursor = returned_cursor
