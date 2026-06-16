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
    """Synchronous wrapper for evaluation routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str,
        chat_id: str | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous evaluation operation."""

        body = EvaluateRequest(
            user_message=user_message,
            ai_answer=ai_answer,
            chat_id=chat_id,
            model_response_id=model_response_id,
            turn_id=turn_id,
        )
        payload = self._transport.request_json(
            "POST",
            "/evaluate",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(exclude_none=True),
        )
        return parse_response(PublicOperationResponse, payload)

    def run(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str | None = None,
        chat_id: str | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
    ) -> OperationRunResult:
        """Create and poll an evaluation operation until terminal."""

        key = idempotency_key or _generated_evaluation_idempotency_key()
        operation = self.create(
            user_message=user_message,
            ai_answer=ai_answer,
            idempotency_key=key,
            chat_id=chat_id,
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
        return operation_run_result(operation=final_operation, idempotency_key=key)

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
    """Asynchronous wrapper for evaluation routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str,
        chat_id: str | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
    ) -> PublicOperationResponse:
        """Create an asynchronous evaluation operation."""

        body = EvaluateRequest(
            user_message=user_message,
            ai_answer=ai_answer,
            chat_id=chat_id,
            model_response_id=model_response_id,
            turn_id=turn_id,
        )
        payload = await self._transport.request_json(
            "POST",
            "/evaluate",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(exclude_none=True),
        )
        return parse_response(PublicOperationResponse, payload)

    async def run(
        self,
        *,
        user_message: str,
        ai_answer: str,
        idempotency_key: str | None = None,
        chat_id: str | None = None,
        model_response_id: str | None = None,
        turn_id: str | None = None,
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
    ) -> OperationRunResult:
        """Create and poll an evaluation operation until terminal."""

        key = idempotency_key or _generated_evaluation_idempotency_key()
        operation = await self.create(
            user_message=user_message,
            ai_answer=ai_answer,
            idempotency_key=key,
            chat_id=chat_id,
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
        return operation_run_result(operation=final_operation, idempotency_key=key)

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
