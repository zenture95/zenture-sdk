"""Typed asynchronous public Run resources."""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, Any

from zenture._contract import (
    ArtifactUploadRequest,
    ArtifactUploadResponse,
    CreateRunRequest,
    ListRunEventsResponse,
    ListRunsResponse,
    PrepareKnowledgeRunRequest,
    PrepareKnowledgeRunResponse,
    PublicRunEvent,
    PublicRunHeartbeat,
    PublicRunResponse,
    PublicRunStreamError,
    PublicRunStreamMessage,
    RecordRunOutcomeRequest,
    SignedUploadResponse,
)
from zenture._resources._utils import idempotency_headers, parse_response, path_segment
from zenture._resources.runs import (
    _add_wait_header,
    _is_retryable_stream_error,
    _is_terminal_status,
    _is_terminal_stream_message,
    _phase_key,
    _run_list_params,
    _RunEventStreamState,
)
from zenture.errors import (
    ZentureAPIError,
    ZenturePollingStoppedError,
    ZenturePollingTimeoutError,
    ZentureTransportError,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Sequence
    from datetime import datetime

    from zenture._transport import AsyncTransport


class AsyncRunsResource:
    """Asynchronous REST and event access for canonical public Runs."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def prepare(
        self,
        *,
        task: str,
        artifact: dict[str, Any],
        idempotency_key: str,
        profile: str = "standard",
    ) -> PrepareKnowledgeRunResponse:
        body = PrepareKnowledgeRunRequest(task=task, artifact=artifact, profile=profile)
        payload = await self._transport.request_json(
            "POST",
            "/runs/prepare",
            headers=idempotency_headers(_phase_key(idempotency_key, "prepare")),
            json=body.model_dump(mode="json", exclude_defaults=True),
        )
        return parse_response(PrepareKnowledgeRunResponse, payload)

    async def create(
        self,
        *,
        proposal_id: str,
        proposal_hash: str,
        idempotency_key: str,
        wait: int | None = None,
    ) -> PublicRunResponse:
        body = CreateRunRequest(proposal_id=proposal_id, proposal_hash=proposal_hash)
        headers = idempotency_headers(_phase_key(idempotency_key, "create"))
        _add_wait_header(headers, wait)
        payload = await self._transport.request_json(
            "POST", "/runs", headers=headers, json=body.model_dump(mode="json")
        )
        return parse_response(PublicRunResponse, payload)

    async def run(
        self,
        *,
        task: str,
        artifact: dict[str, Any],
        idempotency_key: str,
        profile: str = "standard",
        wait: int | None = None,
    ) -> PublicRunResponse:
        proposal = await self.prepare(
            task=task,
            artifact=artifact,
            idempotency_key=idempotency_key,
            profile=profile,
        )
        if not proposal.start_admissible:
            raise ValueError("Prepare proposal is not currently admissible")
        return await self.create(
            proposal_id=str(proposal.proposal_id),
            proposal_hash=proposal.proposal_hash,
            idempotency_key=idempotency_key,
            wait=wait,
        )

    async def list(
        self,
        *,
        status: Sequence[str] | None = None,
        decision: Sequence[str] | None = None,
        profile: Sequence[str] | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 5,
        cursor: str | None = None,
    ) -> ListRunsResponse:
        params = _run_list_params(
            status=status,
            decision=decision,
            profile=profile,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor=cursor,
        )
        payload = await self._transport.request_json("GET", "/runs", params=params)
        return parse_response(ListRunsResponse, payload)

    async def get(self, run_id: str, *, view: str = "summary") -> PublicRunResponse:
        if view not in {"summary", "full"}:
            raise ValueError("view must be summary or full")
        payload = await self._transport.request_json(
            "GET", f"/runs/{path_segment(run_id)}", params={"view": view}
        )
        return parse_response(PublicRunResponse, payload)

    async def list_events(
        self, run_id: str, *, cursor: str | None = None, limit: int = 50
    ) -> ListRunEventsResponse:
        if type(limit) is not int or limit < 1 or limit > 50:
            raise ValueError("limit must be between 1 and 50")
        params = {"limit": str(limit)}
        if cursor is not None:
            if not cursor or len(cursor) > 512:
                raise ValueError("cursor must be between 1 and 512 characters")
            params["cursor"] = cursor
        payload = await self._transport.request_json(
            "GET", f"/runs/{path_segment(run_id)}/events", params=params
        )
        return parse_response(ListRunEventsResponse, payload)

    async def iter_events(
        self,
        run_id: str,
        *,
        last_event_id: str | None = None,
        timeout: float | None = None,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Callable[[], bool] | None = None,
    ) -> AsyncIterator[PublicRunStreamMessage]:
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive")
        deadline = time.monotonic() + timeout if timeout is not None else None
        state = _RunEventStreamState(
            cursor=last_event_id,
            initial_interval=initial_interval,
            max_interval=max_interval,
        )

        while True:
            if callable(stop) and stop():
                raise ZenturePollingStoppedError(operation_id=run_id)
            if deadline is not None and time.monotonic() >= deadline:
                raise ZenturePollingTimeoutError(operation_id=run_id)
            headers = {"Accept": "text/event-stream"}
            if state.cursor is not None:
                headers["Last-Event-ID"] = state.cursor
            progressed = False
            try:
                async with self._transport.stream(
                    "GET", f"/runs/{path_segment(run_id)}/events/stream", headers=headers
                ) as response:
                    async for message in _parse_sse_events_async(response.aiter_lines()):
                        emit, message_progressed = state.accept(message)
                        progressed = progressed or message_progressed
                        if not emit:
                            continue
                        yield message
                        if _is_terminal_stream_message(message):
                            return
                        if isinstance(message, PublicRunStreamError):
                            if message.retryable:
                                break
                            return
            except (ZentureAPIError, ZentureTransportError) as exc:
                if not _is_retryable_stream_error(exc):
                    raise

            if callable(stop) and stop():
                raise ZenturePollingStoppedError(operation_id=run_id)
            if deadline is not None and time.monotonic() >= deadline:
                raise ZenturePollingTimeoutError(operation_id=run_id)
            state.finish_stream(progressed=progressed)
            delay = state.reconnect_interval
            if deadline is not None:
                delay = min(delay, max(0.0, deadline - time.monotonic()))
            if delay > 0:
                await asyncio.sleep(delay)

    async def wait(
        self,
        run_id: str,
        *,
        timeout: float = 120.0,
        initial_interval: float = 1.0,
        max_interval: float = 8.0,
        stop: Any = None,
    ) -> PublicRunResponse:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        deadline = time.monotonic() + timeout
        interval = initial_interval
        while True:
            if callable(stop) and stop():
                raise ZenturePollingStoppedError(operation_id=run_id)
            if time.monotonic() >= deadline:
                raise ZenturePollingTimeoutError(operation_id=run_id)
            result = await self.get(run_id)
            if _is_terminal_status(result.status):
                return result
            await asyncio.sleep(min(interval, max(0.0, deadline - time.monotonic())))
            interval = min(interval * 2, max_interval)

    async def cancel(self, run_id: str, *, idempotency_key: str) -> PublicRunResponse:
        payload = await self._transport.request_json(
            "POST",
            f"/runs/{path_segment(run_id)}/cancel",
            headers=idempotency_headers(idempotency_key),
            json={},
        )
        return parse_response(PublicRunResponse, payload)

    async def record_outcome(
        self,
        run_id: str,
        *,
        outcome: str,
        idempotency_key: str,
        outcome_ref: str | None = None,
    ) -> PublicRunResponse:
        body = RecordRunOutcomeRequest(outcome=outcome, outcome_ref=outcome_ref)
        payload = await self._transport.request_json(
            "POST",
            f"/runs/{path_segment(run_id)}/outcome",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return parse_response(PublicRunResponse, payload)

    async def signed_upload(
        self,
        *,
        file_name: str,
        mime_type: str,
        byte_size: int,
        content_hash: str,
        idempotency_key: str,
    ) -> SignedUploadResponse:
        body = ArtifactUploadRequest(
            file_name=file_name,
            mime_type=mime_type,
            byte_size=byte_size,
            content_hash=content_hash,
        )
        payload = await self._transport.request_json(
            "POST",
            "/run-artifacts/signed-upload",
            headers=idempotency_headers(idempotency_key),
            json=body.model_dump(mode="json"),
        )
        return parse_response(SignedUploadResponse, payload)

    async def attach_artifact(
        self,
        *,
        upload_id: str,
        file_name: str,
        mime_type: str,
        content: bytes,
        content_hash: str,
        idempotency_key: str,
    ) -> ArtifactUploadResponse:
        if not isinstance(content, bytes) or not content:
            raise ValueError("content must be non-empty bytes")
        ArtifactUploadRequest(
            upload_id=upload_id,
            file_name=file_name,
            mime_type=mime_type,
            byte_size=len(content),
            content_hash=content_hash,
        )
        headers = idempotency_headers(idempotency_key)
        headers.update({"Content-Type": mime_type, "X-Upload-ID": upload_id})
        payload = await self._transport.request_json(
            "POST",
            "/run-artifacts",
            headers=headers,
            content=content,
        )
        return parse_response(ArtifactUploadResponse, payload)


async def _parse_sse_events_async(lines: AsyncIterator[str]) -> AsyncIterator[PublicRunStreamMessage]:
    data: list[str] = []
    event_type = ""
    async for raw_line in lines:
        line = str(raw_line)
        if not line:
            if data:
                try:
                    yield _parse_stream_message(
                        json.loads("\n".join(data)), event_type
                    )
                except (TypeError, ValueError):
                    raise ValueError("public Run event stream contained invalid JSON") from None
                data.clear()
                event_type = ""
            continue
        if line.startswith(":") or line.startswith("id:"):
            continue
        if line.startswith("event:"):
            event_type = line[6:].strip()
            continue
        if line.startswith("data:"):
            data.append(line[5:].lstrip())


def _parse_stream_message(payload: object, event_type: str) -> PublicRunStreamMessage:
    if not isinstance(payload, dict):
        raise ValueError("public Run event payload must be an object")
    message_type = payload.get("type") or event_type
    if message_type == "run.event":
        return PublicRunEvent.model_validate(payload)
    if message_type == "run.heartbeat":
        return PublicRunHeartbeat.model_validate(payload)
    if message_type == "run.error":
        return PublicRunStreamError.model_validate(payload)
    raise ValueError("public Run event type is unsupported")


__all__ = ["AsyncRunsResource"]
