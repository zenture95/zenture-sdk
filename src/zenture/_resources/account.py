"""Account and account-adjacent read resource wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenture._contract import (
    LimitsResponse,
    PublicBillingResponse,
    PublicUsageResponse,
    UsageScope,
)
from zenture._resources._utils import parse_response

if TYPE_CHECKING:
    from zenture._transport import AsyncTransport, SyncTransport


class BillingResource:
    """Synchronous wrapper for billing read routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def get(self) -> PublicBillingResponse:
        """Fetch public billing status."""

        payload = self._transport.request_json("GET", "/billing")
        return parse_response(PublicBillingResponse, payload)


class UsageResource:
    """Synchronous wrapper for usage read routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def get(self, *, scope: UsageScope = "api") -> PublicUsageResponse:
        """Fetch public usage counters."""

        payload = self._transport.request_json("GET", "/usage", params={"scope": scope})
        return parse_response(PublicUsageResponse, payload)


class LimitsResource:
    """Synchronous wrapper for limits read routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def get(self) -> LimitsResponse:
        """Fetch public route and operation limits."""

        payload = self._transport.request_json("GET", "/limits")
        return parse_response(LimitsResponse, payload)


class AsyncBillingResource:
    """Asynchronous wrapper for billing read routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def get(self) -> PublicBillingResponse:
        """Fetch public billing status."""

        payload = await self._transport.request_json("GET", "/billing")
        return parse_response(PublicBillingResponse, payload)


class AsyncUsageResource:
    """Asynchronous wrapper for usage read routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def get(self, *, scope: UsageScope = "api") -> PublicUsageResponse:
        """Fetch public usage counters."""

        payload = await self._transport.request_json("GET", "/usage", params={"scope": scope})
        return parse_response(PublicUsageResponse, payload)


class AsyncLimitsResource:
    """Asynchronous wrapper for limits read routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def get(self) -> LimitsResponse:
        """Fetch public route and operation limits."""

        payload = await self._transport.request_json("GET", "/limits")
        return parse_response(LimitsResponse, payload)
