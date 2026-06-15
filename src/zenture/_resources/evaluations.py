"""Evaluation resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenture._contract import (
    EvaluateRequest,
    PublicEvaluationCollectionResponse,
    PublicEvaluationResponse,
    PublicOperationResponse,
)
from zenture._resources._utils import idempotency_headers, parse_response, path_segment

if TYPE_CHECKING:
    from zenture._transport import AsyncTransport, SyncTransport


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

    def list(self) -> PublicEvaluationCollectionResponse:
        """List public evaluations available to the API token."""

        payload = self._transport.request_json("GET", "/evaluations")
        return parse_response(PublicEvaluationCollectionResponse, payload)

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

    async def list(self) -> PublicEvaluationCollectionResponse:
        """List public evaluations available to the API token."""

        payload = await self._transport.request_json("GET", "/evaluations")
        return parse_response(PublicEvaluationCollectionResponse, payload)

    async def get(self, evaluation_id: str) -> PublicEvaluationResponse:
        """Fetch one public evaluation."""

        payload = await self._transport.request_json(
            "GET",
            f"/evaluations/{path_segment(evaluation_id)}",
        )
        return parse_response(PublicEvaluationResponse, payload)
