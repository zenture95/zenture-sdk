"""Evaluation resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from zenture._contract import (
    EvaluateRequest,
    OperationRunResult,
    PublicEvaluationCollectionResponse,
    PublicEvaluationResponse,
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


def _generated_evaluation_idempotency_key() -> str:
    return build_idempotency_key("evaluation", uuid4().hex)


class EvaluationsResource:
    """Synchronous wrapper for evaluation routes.

    Evaluation always needs the pair that should be judged: ``user_message`` and
    ``ai_answer``. If the answer came from zenture chat, also pass the owned
    ``model_response_id`` from the chat result or chat messages response, plus
    optional ``chat_id`` and ``turn_id``. If the answer came from another system,
    omit zenture chat ids and optionally pass your own ``external_id`` and
    bounded ``metadata`` for correlation.
    """

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str,
        chat_id: str | None = None,
        external_id: str | None = None,
        metadata: dict[str, object] | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous evaluation operation.

        Use ``model_response_id`` for an existing zenture chat answer. Without a
        ``model_response_id``, the request is treated as an external
        evaluation-only record and is not added to zenture chat history.

        ``idempotency_key`` is caller-owned and required for retry safety. Reuse
        the same key only when retrying the same request body.
        """

        body = EvaluateRequest(
            user_message=user_message,
            ai_answer=ai_answer,
            external_id=external_id,
            metadata=metadata or {},
            chat_id=chat_id,
            model_response_id=model_response_id,
            turn_id=turn_id,
        )
        payload = self._transport.request_json(
            "POST",
            "/evaluate",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(exclude_none=True, exclude_defaults=True),
        )
        return parse_response(PublicOperationResponse, payload)

    def run(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str | None = None,
        chat_id: str | None = None,
        external_id: str | None = None,
        metadata: dict[str, object] | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
        include_detail: bool = False,
    ) -> OperationRunResult:
        """Create and poll an evaluation operation until terminal.

        Internal chat answer:
            pass ``user_message``, ``ai_answer``, ``chat_id``, ``turn_id``, and
            the AI-answer ``model_response_id``.

        External answer:
            pass ``user_message`` and ``ai_answer`` only, with optional
            ``external_id``/``metadata``. Do not pass zenture chat ids for
            external content.

        When ``idempotency_key`` is omitted this helper generates one and
        returns it on the ``OperationRunResult``. For application retries,
        prefer a stable key from your own system. Set ``include_detail=True``
        to attach the public evaluation detail as ``evaluation`` after success.
        """

        key = idempotency_key or _generated_evaluation_idempotency_key()
        operation = self.create(
            user_message=user_message,
            ai_answer=ai_answer,
            idempotency_key=key,
            chat_id=chat_id,
            external_id=external_id,
            metadata=metadata,
            model_response_id=model_response_id,
            turn_id=turn_id,
        )
        try:
            final_operation = OperationsResource(self._transport).wait(
                operation.operation_id,
                timeout=timeout,
                initial_interval=initial_interval,
                max_interval=max_interval,
                stop=stop,
            )
        except (ZenturePollingTimeoutError, ZenturePollingStoppedError) as exc:
            raise polling_error_with_context(
                exc,
                operation_id=operation.operation_id,
                idempotency_key=key,
            ) from None
        run_result = operation_run_result(operation=final_operation, idempotency_key=key)
        if (
            not include_detail
            or run_result.result is None
            or run_result.result.evaluation_id is None
        ):
            return run_result
        return run_result.model_copy(
            update={"evaluation": self.get(run_result.result.evaluation_id)}
        )

    def list(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PublicEvaluationCollectionResponse:
        """List public evaluations available to the API token."""

        payload = self._transport.request_json(
            "GET",
            "/evaluations",
            params=pagination_params(limit=limit, cursor=cursor),
        )
        return parse_response(PublicEvaluationCollectionResponse, payload)

    def iter(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> Iterator[PublicEvaluationResponse]:
        """Iterate public evaluations until the API returns no next cursor."""

        next_cursor = cursor
        while True:
            page = self.list(limit=limit, cursor=next_cursor)
            yield from page.evaluations
            if page.next_cursor is None:
                return
            next_cursor = page.next_cursor

    def get(self, evaluation_id: str) -> PublicEvaluationResponse:
        """Fetch one public evaluation."""

        payload = self._transport.request_json(
            "GET",
            f"/evaluations/{path_segment(evaluation_id)}",
        )
        return parse_response(PublicEvaluationResponse, payload)


class AsyncEvaluationsResource:
    """Asynchronous wrapper for evaluation routes.

    Evaluation always needs the pair that should be judged: ``user_message`` and
    ``ai_answer``. Pass ``model_response_id`` only for existing owned zenture
    chat answers. Omit zenture chat ids for external answers and use optional
    ``external_id``/``metadata`` for caller-side correlation.
    """

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str,
        chat_id: str | None = None,
        external_id: str | None = None,
        metadata: dict[str, object] | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous evaluation operation.

        ``model_response_id`` selects the internal zenture chat-answer path.
        Without it, the request creates an external evaluation-only record that
        does not appear in normal chat history. ``idempotency_key`` is required
        and must be stable across retries of the same body.
        """

        body = EvaluateRequest(
            user_message=user_message,
            ai_answer=ai_answer,
            external_id=external_id,
            metadata=metadata or {},
            chat_id=chat_id,
            model_response_id=model_response_id,
            turn_id=turn_id,
        )
        payload = await self._transport.request_json(
            "POST",
            "/evaluate",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(exclude_none=True, exclude_defaults=True),
        )
        return parse_response(PublicOperationResponse, payload)

    async def run(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str | None = None,
        chat_id: str | None = None,
        external_id: str | None = None,
        metadata: dict[str, object] | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
        include_detail: bool = False,
    ) -> OperationRunResult:
        """Create and poll an evaluation operation until terminal.

        For zenture chat answers, pass ``chat_id``, ``turn_id``, and
        ``model_response_id`` with the turn's ``user_message`` and
        ``model_answer``. For external answers, omit zenture chat ids and pass
        optional ``external_id``/``metadata`` only for correlation. Set
        ``include_detail=True`` to attach the public evaluation detail as
        ``evaluation`` after success.
        """

        key = idempotency_key or _generated_evaluation_idempotency_key()
        operation = await self.create(
            user_message=user_message,
            ai_answer=ai_answer,
            idempotency_key=key,
            chat_id=chat_id,
            external_id=external_id,
            metadata=metadata,
            model_response_id=model_response_id,
            turn_id=turn_id,
        )
        try:
            final_operation = await AsyncOperationsResource(self._transport).wait(
                operation.operation_id,
                timeout=timeout,
                initial_interval=initial_interval,
                max_interval=max_interval,
                stop=stop,
            )
        except (ZenturePollingTimeoutError, ZenturePollingStoppedError) as exc:
            raise polling_error_with_context(
                exc,
                operation_id=operation.operation_id,
                idempotency_key=key,
            ) from None
        run_result = operation_run_result(operation=final_operation, idempotency_key=key)
        if (
            not include_detail
            or run_result.result is None
            or run_result.result.evaluation_id is None
        ):
            return run_result
        return run_result.model_copy(
            update={"evaluation": await self.get(run_result.result.evaluation_id)}
        )

    async def list(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PublicEvaluationCollectionResponse:
        """List public evaluations available to the API token."""

        payload = await self._transport.request_json(
            "GET",
            "/evaluations",
            params=pagination_params(limit=limit, cursor=cursor),
        )
        return parse_response(PublicEvaluationCollectionResponse, payload)

    async def iter(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> AsyncIterator[PublicEvaluationResponse]:
        """Iterate public evaluations until the API returns no next cursor."""

        next_cursor = cursor
        while True:
            page = await self.list(limit=limit, cursor=next_cursor)
            for evaluation in page.evaluations:
                yield evaluation
            if page.next_cursor is None:
                return
            next_cursor = page.next_cursor

    async def get(self, evaluation_id: str) -> PublicEvaluationResponse:
        """Fetch one public evaluation."""

        payload = await self._transport.request_json(
            "GET",
            f"/evaluations/{path_segment(evaluation_id)}",
        )
        return parse_response(PublicEvaluationResponse, payload)
