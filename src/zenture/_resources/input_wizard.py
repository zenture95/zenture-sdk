"""Input wizard resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from zenture._contract import InputWizardRequest, PublicOperationResponse
from zenture._resources._utils import idempotency_headers, parse_response

if TYPE_CHECKING:
    from zenture._transport import AsyncTransport, SyncTransport


class InputWizardResource:
    """Synchronous wrapper for input wizard routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        prompt: str,
        idempotency_key: str,
        mode: Literal["prompt_improvement"] = "prompt_improvement",
    ) -> PublicOperationResponse:
        """Create an asynchronous input wizard operation."""

        body = InputWizardRequest(mode=mode, prompt=prompt)
        payload = self._transport.request_json(
            "POST",
            "/input-wizard",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(),
        )
        return parse_response(PublicOperationResponse, payload)


class AsyncInputWizardResource:
    """Asynchronous wrapper for input wizard routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        prompt: str,
        idempotency_key: str,
        mode: Literal["prompt_improvement"] = "prompt_improvement",
    ) -> PublicOperationResponse:
        """Create an asynchronous input wizard operation."""

        body = InputWizardRequest(mode=mode, prompt=prompt)
        payload = await self._transport.request_json(
            "POST",
            "/input-wizard",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(),
        )
        return parse_response(PublicOperationResponse, payload)
