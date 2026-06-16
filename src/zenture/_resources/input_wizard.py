"""Input wizard resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from zenture._contract import InputWizardRequest, OperationRunResult, PublicOperationResponse
from zenture._resources._utils import (
    idempotency_headers,
    operation_run_result,
    parse_response,
    polling_error_with_context,
)
from zenture._resources.operations import AsyncOperationsResource, OperationsResource
from zenture.errors import ZenturePollingStoppedError, ZenturePollingTimeoutError
from zenture.idempotency import idempotency_key as build_idempotency_key

if TYPE_CHECKING:
    from collections.abc import Callable

    from zenture._transport import AsyncTransport, SyncTransport


def _generated_input_wizard_idempotency_key() -> str:
    return build_idempotency_key("input-wizard", uuid4().hex)


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

    def run(
        self,
        *,
        prompt: str,
        idempotency_key: str | None = None,
        mode: Literal["prompt_improvement"] = "prompt_improvement",
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
    ) -> OperationRunResult:
        """Create and poll an input wizard operation until terminal."""

        key = idempotency_key or _generated_input_wizard_idempotency_key()
        operation = self.create(prompt=prompt, idempotency_key=key, mode=mode)
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

    async def run(
        self,
        *,
        prompt: str,
        idempotency_key: str | None = None,
        mode: Literal["prompt_improvement"] = "prompt_improvement",
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
    ) -> OperationRunResult:
        """Create and poll an input wizard operation until terminal."""

        key = idempotency_key or _generated_input_wizard_idempotency_key()
        operation = await self.create(prompt=prompt, idempotency_key=key, mode=mode)
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
