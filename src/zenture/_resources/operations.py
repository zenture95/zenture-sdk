"""Operation resource wrappers."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from zenture._contract import PublicOperationResponse
from zenture._resources._utils import parse_response, path_segment
from zenture.errors import ZenturePollingStoppedError, ZenturePollingTimeoutError
from zenture.polling import (
    PollingConfig,
    is_terminal_status,
    next_poll_interval,
    remaining_timeout,
    should_stop_polling,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from zenture._transport import AsyncTransport, SyncTransport


def sleep_for_polling(seconds: float) -> None:
    """Sleep between sync operation polls."""

    time.sleep(seconds)


async def async_sleep_for_polling(seconds: float) -> None:
    """Sleep between async operation polls."""

    await asyncio.sleep(seconds)


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

    def wait(
        self,
        operation_id: str,
        *,
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
    ) -> PublicOperationResponse:
        """Poll one operation until it reaches a terminal status."""

        config = PollingConfig(
            timeout=timeout,
            initial_interval=initial_interval,
            max_interval=max_interval,
        )
        deadline = time.monotonic() + config.timeout
        interval = config.initial_interval

        while True:
            if should_stop_polling(stop):
                raise ZenturePollingStoppedError(operation_id=operation_id)

            remaining = remaining_timeout(deadline=deadline, now=time.monotonic())
            if remaining <= 0:
                raise ZenturePollingTimeoutError(operation_id=operation_id)

            operation = self.get(operation_id)
            if is_terminal_status(operation.status):
                return operation

            remaining = remaining_timeout(deadline=deadline, now=time.monotonic())
            if remaining <= 0:
                raise ZenturePollingTimeoutError(operation_id=operation_id)
            sleep_for_polling(min(interval, remaining))
            interval = next_poll_interval(current=interval, max_interval=config.max_interval)


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

    async def wait(
        self,
        operation_id: str,
        *,
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
    ) -> PublicOperationResponse:
        """Poll one operation until it reaches a terminal status."""

        config = PollingConfig(
            timeout=timeout,
            initial_interval=initial_interval,
            max_interval=max_interval,
        )
        deadline = time.monotonic() + config.timeout
        interval = config.initial_interval

        while True:
            if should_stop_polling(stop):
                raise ZenturePollingStoppedError(operation_id=operation_id)

            remaining = remaining_timeout(deadline=deadline, now=time.monotonic())
            if remaining <= 0:
                raise ZenturePollingTimeoutError(operation_id=operation_id)

            operation = await self.get(operation_id)
            if is_terminal_status(operation.status):
                return operation

            remaining = remaining_timeout(deadline=deadline, now=time.monotonic())
            if remaining <= 0:
                raise ZenturePollingTimeoutError(operation_id=operation_id)
            await async_sleep_for_polling(min(interval, remaining))
            interval = next_poll_interval(current=interval, max_interval=config.max_interval)
