"""Asynchronous HTTPX transport wrapper."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast

import httpx

from zenture._transport.base import (
    build_timeout,
    build_url,
    default_headers,
    extract_error_code,
    has_idempotency_key,
    retry_delay,
)
from zenture.errors import (
    ZentureAPIError,
    ZentureResponseError,
    ZentureTransportError,
    error_from_response,
)
from zenture.redaction import redact_text
from zenture.retries import should_retry

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from zenture.config import ZentureConfig


class AsyncTransport:
    """Owns or wraps an asynchronous HTTPX client."""

    def __init__(
        self,
        *,
        config: ZentureConfig,
        client: httpx.AsyncClient | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=config.api_base_url,
            timeout=build_timeout(config),
        )
        self._config = config
        self._user_agent = user_agent

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    def _request_headers(self, *, auth: bool = True) -> dict[str, str]:
        return default_headers(self._config, self._user_agent, auth=auth)

    async def request_text(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        headers: dict[str, str] | None = None,
        json: object | None = None,
        params: dict[str, str] | None = None,
    ) -> str:
        """Request a text response and map public API errors."""

        response = await self._request(
            method,
            path,
            auth=auth,
            headers=headers,
            json=json,
            params=params,
        )
        return response.text

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        headers: dict[str, str] | None = None,
        json: object | None = None,
        params: dict[str, str] | None = None,
    ) -> object:
        """Request a JSON response and map public API errors."""

        response = await self._request(
            method,
            path,
            auth=auth,
            headers=headers,
            json=json,
            params=params,
        )
        response_error: ZentureResponseError | None = None
        try:
            return response.json()
        except ValueError:
            response_error = ZentureResponseError("Public API response was not valid JSON.")
        raise response_error

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> AsyncIterator[httpx.Response]:
        """Open one non-buffered public stream without mutation retries."""

        request_headers = self._request_headers(auth=auth)
        if headers is not None:
            request_headers.update(headers)
        try:
            async with self._client.stream(
                method,
                build_url(self._config, path),
                headers=request_headers,
                params=params,
            ) as response:
                if response.status_code >= 400:
                    await _raise_stream_error(response)
                yield response
        except (ZentureResponseError, ZentureAPIError):
            raise
        except httpx.HTTPError as exc:
            raise ZentureTransportError(redact_text(str(exc))) from exc

    async def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool,
        headers: dict[str, str] | None,
        json: object | None,
        params: dict[str, str] | None,
    ) -> httpx.Response:
        request_headers = self._request_headers(auth=auth)
        if headers is not None:
            request_headers.update(headers)

        attempt = 1
        max_attempts = self._config.max_retries + 1
        while True:
            response: httpx.Response | None = None
            transport_error: ZentureTransportError | None = None
            try:
                response = await self._client.request(
                    method,
                    build_url(self._config, path),
                    headers=request_headers,
                    json=json,
                    params=params,
                )
            except httpx.HTTPError as exc:
                decision = should_retry(
                    method=method,
                    status_code=503,
                    error_code="dependency_unavailable",
                    has_idempotency_key=has_idempotency_key(request_headers),
                    attempt=attempt,
                    max_attempts=max_attempts,
                )
                if decision.retry:
                    delay = retry_delay(
                        retry_after=None,
                        attempt=attempt,
                        initial_backoff=self._config.initial_retry_backoff,
                        max_backoff=self._config.max_retry_backoff,
                    )
                    if delay > 0:
                        await asyncio.sleep(delay)
                    attempt += 1
                    continue
                transport_error = ZentureTransportError(redact_text(str(exc)))
            if transport_error is not None:
                raise transport_error
            assert response is not None

            if response.status_code < 400:
                return response

            payload: object | None = None
            response_error: ZentureResponseError | None = None
            try:
                payload = response.json()
            except ValueError:
                response_error = ZentureResponseError(
                    "Public API error response was not valid JSON."
                )
            if response_error is not None:
                raise response_error
            assert payload is not None
            if not isinstance(payload, dict):
                raise ZentureResponseError("Public API error response was not an object.")
            payload_dict = cast("dict[str, object]", payload)

            decision = should_retry(
                method=method,
                status_code=response.status_code,
                error_code=extract_error_code(payload_dict),
                has_idempotency_key=has_idempotency_key(request_headers),
                attempt=attempt,
                max_attempts=max_attempts,
            )
            if decision.retry:
                delay = retry_delay(
                    retry_after=response.headers.get("Retry-After"),
                    attempt=attempt,
                    initial_backoff=self._config.initial_retry_backoff,
                    max_backoff=self._config.max_retry_backoff,
                )
                if delay > 0:
                    await asyncio.sleep(delay)
                attempt += 1
                continue

            raise error_from_response(
                status_code=response.status_code,
                payload=payload_dict,
                headers=response.headers,
            )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()


async def _raise_stream_error(response: httpx.Response) -> None:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ZentureResponseError("Public API error response was not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ZentureResponseError("Public API error response was not an object.")
    raise error_from_response(
        status_code=response.status_code,
        payload=payload,
        headers=response.headers,
    )
