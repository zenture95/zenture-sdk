"""Local REST and SSE contract tests for the public Run resources."""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import time
from types import SimpleNamespace

import httpx
import pytest

from zenture import AsyncZenture, Zenture
from zenture._contract import PublicRunEvent, PublicRunHeartbeat
from zenture._resources.runs import _RunEventStreamState
from zenture.errors import (
    ZenturePollingStoppedError,
    ZenturePollingTimeoutError,
    ZentureTransportError,
)

API_KEY = "zt_live_runs_test_abcdefghijklmnopqrstuvwxyz0123456789"
RUN_ID = "run_33333333333343338333333333333333"
PROPOSAL_ID = "33333333-3333-4333-8333-333333333333"


def _proposal() -> dict[str, object]:
    return {
        "proposal_id": PROPOSAL_ID,
        "proposal_version": 1,
        "expires_at": "2026-08-30T12:30:00Z",
        "inferred_work_type": "answer",
        "task_contract_summary": {
            "work_type": "answer",
            "summary_ref": "snapshot:task-summary-v1",
            "requirement_count": 1,
        },
        "planned_checks": ["check:material-claims"],
        "unavailable_checks": [],
        "expected_duration_seconds": 30,
        "estimated_credits": "12",
        "maximum_credits": "24",
        "start_admissible": True,
        "proposal_hash": "a" * 64,
    }


def _run(*, status: str = "queued") -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "generation": 1,
        "family": "knowledge",
        "work_type": "answer",
        "profile": "standard",
        "status": status,
        "created_at": "2026-08-30T12:00:00Z",
        "updated_at": "2026-08-30T12:00:00Z",
        "queue": {"queue_reason": "queue:admitted", "jobs_ahead": 0},
        "cancellation_requested": False,
    }


def _sse_event(*, event_id: str, sequence: int, status: str, event_cursor: str) -> bytes:
    payload = {
        "type": "run.event",
        "event_id": event_id,
        "run_id": RUN_ID,
        "sequence": sequence,
        "phase": status,
        "status": status,
        "message_key": f"run.status.{status}",
        "event_cursor": event_cursor,
    }
    return f"event: run.event\ndata: {json.dumps(payload)}\n\n".encode()


def _sse_error(*, event_id: str, sequence: int, retryable: bool) -> bytes:
    payload = {
        "type": "run.error",
        "event_id": event_id,
        "run_id": RUN_ID,
        "sequence": sequence,
        "code": "dependency_unavailable",
        "message": "stream temporarily unavailable",
        "retryable": retryable,
        "terminal": not retryable,
    }
    return f"event: run.error\ndata: {json.dumps(payload)}\n\n".encode()


def _sse_heartbeat(*, event_id: str, sequence: int) -> bytes:
    payload = {
        "type": "run.heartbeat",
        "event_id": event_id,
        "run_id": RUN_ID,
        "sequence": sequence,
    }
    return f"event: run.heartbeat\ndata: {json.dumps(payload)}\n\n".encode()


def _stream_response(*parts: bytes) -> httpx.Response:
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        content=b"".join(parts),
    )


def _reconnect_responses() -> list[httpx.Response]:
    return [
        _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="running",
                event_cursor="cursor_aaa",
            )
        ),
        _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="running",
                event_cursor="cursor_aaa",
            ),
            _sse_event(
                event_id="event_bbb",
                sequence=1,
                status="running",
                event_cursor="cursor_bbb",
            ),
            _sse_event(
                event_id="event_aaa",
                sequence=2,
                status="running",
                event_cursor="cursor_ccc",
            ),
            _sse_error(event_id="error_aaa", sequence=4, retryable=True),
        ),
        _stream_response(
            _sse_event(
                event_id="event_ccc",
                sequence=3,
                status="completed",
                event_cursor="cursor_ddd",
            )
        ),
    ]


def test_sync_iter_events_reconnects_deduplicates_and_stops_at_terminal() -> None:
    responses = _reconnect_responses()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        requests.append(request)
        return responses[min(len(responses) - 1, len(requests) - 1)]

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    messages = list(client.runs.iter_events(RUN_ID, initial_interval=0.0, max_interval=0.0))

    assert [message.event_id for message in messages] == [
        "event_aaa",
        "error_aaa",
        "event_ccc",
    ]
    assert len(requests) == 3
    assert requests[1].headers["last-event-id"] == "cursor_aaa"
    assert requests[2].headers["last-event-id"] == "cursor_aaa"
    client.close()


@pytest.mark.asyncio
async def test_async_iter_events_reconnects_deduplicates_and_stops_at_terminal() -> None:
    responses = _reconnect_responses()
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        requests.append(request)
        return responses[min(len(responses) - 1, len(requests) - 1)]

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    messages = [
        message
        async for message in client.runs.iter_events(RUN_ID, initial_interval=0.0, max_interval=0.0)
    ]

    assert [message.event_id for message in messages] == [
        "event_aaa",
        "error_aaa",
        "event_ccc",
    ]
    assert len(requests) == 3
    assert requests[1].headers["last-event-id"] == "cursor_aaa"
    assert requests[2].headers["last-event-id"] == "cursor_aaa"
    await client.aclose()


def test_sync_iter_events_reconnects_after_retryable_transport_error() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        requests.append(request)
        if len(requests) == 1:
            raise httpx.ReadError("stream reset")
        return _stream_response(
            _sse_event(
                event_id="event_bbb",
                sequence=2,
                status="completed",
                event_cursor="cursor_bbb",
            )
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    messages = list(client.runs.iter_events(RUN_ID, initial_interval=0.0, max_interval=0.0))

    assert [message.event_id for message in messages] == ["event_bbb"]
    assert len(requests) == 2
    client.close()


@pytest.mark.asyncio
async def test_async_iter_events_reconnects_after_retryable_transport_error() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        requests.append(request)
        if len(requests) == 1:
            raise httpx.ReadError("stream reset")
        return _stream_response(
            _sse_event(
                event_id="event_bbb",
                sequence=2,
                status="completed",
                event_cursor="cursor_bbb",
            )
        )

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    messages = [
        message
        async for message in client.runs.iter_events(RUN_ID, initial_interval=0.0, max_interval=0.0)
    ]

    assert [message.event_id for message in messages] == ["event_bbb"]
    assert len(requests) == 2
    await client.aclose()


def test_sync_iter_events_stops_on_caller_stop() -> None:
    requests: list[httpx.Request] = []
    stop_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="running",
                event_cursor="cursor_aaa",
            )
        )

    def stop() -> bool:
        nonlocal stop_calls
        stop_calls += 1
        return stop_calls > 1

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZenturePollingStoppedError):
        list(client.runs.iter_events(RUN_ID, stop=stop, initial_interval=0.0, max_interval=0.0))

    assert len(requests) == 1
    client.close()


@pytest.mark.asyncio
async def test_async_iter_events_stops_on_caller_timeout() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="running",
                event_cursor="cursor_aaa",
            )
        )

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZenturePollingTimeoutError):
        [
            message
            async for message in client.runs.iter_events(
                RUN_ID, timeout=0.005, initial_interval=0.01, max_interval=0.01
            )
        ]

    assert len(requests) == 1
    await client.aclose()


def test_sync_iter_events_bounds_cursor_cycles() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="running",
                event_cursor="cursor_aaa",
            )
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZentureTransportError, match="bounded"):
        list(client.runs.iter_events(RUN_ID, initial_interval=0.0, max_interval=0.0))

    assert 1 < len(requests) < 10
    client.close()


@pytest.mark.asyncio
async def test_async_iter_events_bounds_cursor_cycles() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="running",
                event_cursor="cursor_aaa",
            )
        )

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZentureTransportError, match="bounded"):
        [
            message
            async for message in client.runs.iter_events(
                RUN_ID, initial_interval=0.0, max_interval=0.0
            )
        ]

    assert 1 < len(requests) < 10
    await client.aclose()


def _artifact_response(content: bytes) -> httpx.Response:
    return httpx.Response(
        201,
        json={
            "artifact_ref": "art_abcdefgh",
            "content_hash": hashlib.sha256(content).hexdigest(),
            "byte_size": len(content),
            "content_type": "application/pdf",
        },
    )


def test_sync_attach_artifact_streams_iterable_with_declared_size_and_hash() -> None:
    content = b"streamed bytes"
    chunks = iter((content[:8], content[8:]))

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-length"] == str(len(content))
        assert request.read() == content
        return _artifact_response(content)

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.runs.attach_artifact(
        upload_id="upload_abcdefgh",
        file_name="answer.pdf",
        mime_type="application/pdf",
        content=chunks,
        byte_size=len(content),
        content_hash=hashlib.sha256(content).hexdigest(),
        idempotency_key="artifact-stream-1",
    )

    assert result.artifact_ref == "art_abcdefgh"
    client.close()


@pytest.mark.asyncio
async def test_async_attach_artifact_streams_async_iterable_with_declared_size_and_hash() -> None:
    content = b"async streamed bytes"

    async def chunks():
        yield content[:5]
        yield content[5:]

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-length"] == str(len(content))
        assert await request.aread() == content
        return _artifact_response(content)

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await client.runs.attach_artifact(
        upload_id="upload_abcdefgh",
        file_name="answer.pdf",
        mime_type="application/pdf",
        content=chunks(),
        byte_size=len(content),
        content_hash=hashlib.sha256(content).hexdigest(),
        idempotency_key="artifact-stream-1",
    )

    assert result.artifact_ref == "art_abcdefgh"
    await client.aclose()


def test_sync_attach_artifact_streams_file_without_closing_caller_source() -> None:
    content = b"sync file bytes"
    source = io.BytesIO(content)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.read() == content
        return _artifact_response(content)

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.runs.attach_artifact(
        upload_id="upload_abcdefgh",
        file_name="answer.pdf",
        mime_type="application/pdf",
        content=source,
        byte_size=len(content),
        content_hash=hashlib.sha256(content).hexdigest(),
        idempotency_key="artifact-file-1",
    )

    assert result.artifact_ref == "art_abcdefgh"
    assert not source.closed
    client.close()


@pytest.mark.asyncio
async def test_async_attach_artifact_streams_file_without_closing_caller_source() -> None:
    content = b"async file bytes"
    source = io.BytesIO(content)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert await request.aread() == content
        return _artifact_response(content)

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await client.runs.attach_artifact(
        upload_id="upload_abcdefgh",
        file_name="answer.pdf",
        mime_type="application/pdf",
        content=source,
        byte_size=len(content),
        content_hash=hashlib.sha256(content).hexdigest(),
        idempotency_key="artifact-file-1",
    )

    assert result.artifact_ref == "art_abcdefgh"
    assert not source.closed
    await client.aclose()


def test_sync_attach_artifact_rejects_size_overrun_and_hash_mismatch() -> None:
    content = b"bytes"

    def handler(request: httpx.Request) -> httpx.Response:
        request.read()
        return _artifact_response(content)

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ValueError, match="exceeds declared byte_size"):
        client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=iter((b"bytes", b"extra")),
            byte_size=len(content),
            content_hash=hashlib.sha256(content + b"extra").hexdigest(),
            idempotency_key="artifact-stream-6",
        )
    with pytest.raises(ValueError, match="content_hash"):
        client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=iter((content,)),
            byte_size=len(content),
            content_hash=hashlib.sha256(b"other").hexdigest(),
            idempotency_key="artifact-stream-7",
        )

    client.close()


@pytest.mark.asyncio
async def test_async_attach_artifact_rejects_size_overrun_and_hash_mismatch() -> None:
    content = b"bytes"

    async def overrun_chunks():
        yield content
        yield b"extra"

    async def bad_hash_chunks():
        yield content

    async def handler(request: httpx.Request) -> httpx.Response:
        await request.aread()
        return _artifact_response(content)

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ValueError, match="exceeds declared byte_size"):
        await client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=overrun_chunks(),
            byte_size=len(content),
            content_hash=hashlib.sha256(content + b"extra").hexdigest(),
            idempotency_key="artifact-stream-6",
        )
    with pytest.raises(ValueError, match="content_hash"):
        await client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=bad_hash_chunks(),
            byte_size=len(content),
            content_hash=hashlib.sha256(b"other").hexdigest(),
            idempotency_key="artifact-stream-7",
        )

    await client.aclose()


def test_sync_attach_artifact_rejects_stream_without_declared_size() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _artifact_response(b"bytes")

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ValueError, match="byte_size"):
        client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=iter((b"bytes",)),
            content_hash=hashlib.sha256(b"bytes").hexdigest(),
            idempotency_key="artifact-stream-2",
        )

    assert not requests
    client.close()


@pytest.mark.asyncio
async def test_async_attach_artifact_rejects_stream_without_declared_size() -> None:
    requests: list[httpx.Request] = []

    async def chunks():
        yield b"bytes"

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _artifact_response(b"bytes")

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ValueError, match="byte_size"):
        await client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=chunks(),
            content_hash=hashlib.sha256(b"bytes").hexdigest(),
            idempotency_key="artifact-stream-2",
        )

    assert not requests
    await client.aclose()


def test_sync_attach_artifact_rejects_non_bytes_chunk() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        request.read()
        return _artifact_response(b"bytes")

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ValueError, match="chunks must be bytes"):
        client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=iter((b"byte", "s")),
            byte_size=5,
            content_hash=hashlib.sha256(b"bytes").hexdigest(),
            idempotency_key="artifact-stream-3",
        )

    client.close()


@pytest.mark.asyncio
async def test_async_attach_artifact_rejects_non_bytes_chunk() -> None:
    async def chunks():
        yield b"byte"
        yield "s"

    async def handler(request: httpx.Request) -> httpx.Response:
        await request.aread()
        return _artifact_response(b"bytes")

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ValueError, match="chunks must be bytes"):
        await client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=chunks(),
            byte_size=5,
            content_hash=hashlib.sha256(b"bytes").hexdigest(),
            idempotency_key="artifact-stream-3",
        )

    await client.aclose()


def test_sync_attach_artifact_does_not_retry_one_shot_file() -> None:
    content = b"one-shot bytes"
    source = io.BytesIO(content)
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadError("upload connection reset")

    client = Zenture(
        api_key=API_KEY,
        max_retries=2,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZentureTransportError):
        client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=source,
            byte_size=len(content),
            content_hash=hashlib.sha256(content).hexdigest(),
            idempotency_key="artifact-stream-4",
        )

    assert attempts == 1
    assert not source.closed
    client.close()


@pytest.mark.asyncio
async def test_async_attach_artifact_does_not_retry_one_shot_file() -> None:
    content = b"one-shot async bytes"
    source = io.BytesIO(content)
    attempts = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadError("upload connection reset")

    client = AsyncZenture(
        api_key=API_KEY,
        max_retries=2,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZentureTransportError):
        await client.runs.attach_artifact(
            upload_id="upload_abcdefgh",
            file_name="answer.pdf",
            mime_type="application/pdf",
            content=source,
            byte_size=len(content),
            content_hash=hashlib.sha256(content).hexdigest(),
            idempotency_key="artifact-stream-4",
        )

    assert attempts == 1
    assert not source.closed
    await client.aclose()


def test_sync_attach_artifact_retries_replayable_bytes() -> None:
    content = b"replayable bytes"
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadError("upload connection reset")
        assert request.read() == content
        return _artifact_response(content)

    client = Zenture(
        api_key=API_KEY,
        max_retries=1,
        initial_retry_backoff=0.0,
        max_retry_backoff=0.0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.runs.attach_artifact(
        upload_id="upload_abcdefgh",
        file_name="answer.pdf",
        mime_type="application/pdf",
        content=content,
        content_hash=hashlib.sha256(content).hexdigest(),
        idempotency_key="artifact-stream-5",
    )

    assert result.artifact_ref == "art_abcdefgh"
    assert attempts == 2
    client.close()


@pytest.mark.asyncio
async def test_async_attach_artifact_retries_replayable_bytes() -> None:
    content = b"replayable async bytes"
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadError("upload connection reset")
        assert await request.aread() == content
        return _artifact_response(content)

    client = AsyncZenture(
        api_key=API_KEY,
        max_retries=1,
        initial_retry_backoff=0.0,
        max_retry_backoff=0.0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await client.runs.attach_artifact(
        upload_id="upload_abcdefgh",
        file_name="answer.pdf",
        mime_type="application/pdf",
        content=content,
        content_hash=hashlib.sha256(content).hexdigest(),
        idempotency_key="artifact-stream-5",
    )

    assert result.artifact_ref == "art_abcdefgh"
    assert attempts == 2
    await client.aclose()


def test_sync_wait_returns_when_queued_run_reaches_completed() -> None:
    responses = [_run(), _run(status="completed")]
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/v1/runs/{RUN_ID}"
        seen.append(request)
        return httpx.Response(200, json=responses[min(len(responses) - 1, len(seen) - 1)])

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.runs.wait(
        RUN_ID,
        timeout=0.02,
        initial_interval=0.001,
        max_interval=0.001,
    )

    assert result.status.value == "completed"
    assert len(seen) == 2
    client.close()


@pytest.mark.asyncio
async def test_async_wait_returns_when_queued_run_reaches_completed() -> None:
    responses = [_run(), _run(status="completed")]
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/v1/runs/{RUN_ID}"
        seen.append(request)
        return httpx.Response(200, json=responses[min(len(responses) - 1, len(seen) - 1)])

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await client.runs.wait(
        RUN_ID,
        timeout=0.02,
        initial_interval=0.001,
        max_interval=0.001,
    )

    assert result.status.value == "completed"
    assert len(seen) == 2
    await client.aclose()


def test_sync_run_helper_preserves_idempotency_and_wait_hint() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/runs/prepare"):
            return httpx.Response(200, json=_proposal())
        assert request.url.path.endswith("/runs")
        assert request.headers["idempotency-key"] == "run-1:create"
        assert request.headers["prefer"] == "wait=15"
        return httpx.Response(202, json=_run())

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.runs.run(
        task="Review this answer.",
        artifact={"type": "text", "value": "Selected answer"},
        idempotency_key="run-1",
        wait=99,
    )

    assert result.run_id == RUN_ID
    assert seen[0].headers["idempotency-key"] == "run-1:prepare"
    client.close()


def test_sync_run_sse_parser_supports_event_and_heartbeat() -> None:
    stream = b"""event: run.event
data: {\"type\":\"run.event\",\"event_id\":\"event_aaaaaaaa\",\"run_id\":\"run_33333333333343338333333333333333\",\"sequence\":1,\"phase\":\"queued\",\"status\":\"queued\",\"message_key\":\"run.status.queued\",\"event_cursor\":\"cursor_aaa\"}

event: run.heartbeat
data: {\"type\":\"run.heartbeat\",\"event_id\":\"heartbeat_aaa\",\"run_id\":\"run_33333333333343338333333333333333\",\"sequence\":1}

event: run.event
data: {\"type\":\"run.event\",\"event_id\":\"event_bbbbbbbb\",\"run_id\":\"run_33333333333343338333333333333333\",\"sequence\":2,\"phase\":\"completed\",\"status\":\"completed\",\"message_key\":\"run.status.completed\",\"event_cursor\":\"cursor_bbb\"}

"""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "text/event-stream"
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=stream)

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    messages = list(client.runs.iter_events(RUN_ID))

    assert isinstance(messages[0], PublicRunEvent)
    assert isinstance(messages[1], PublicRunHeartbeat)
    client.close()


def test_sync_attach_artifact_sends_bytes_with_upload_intent() -> None:
    content = b"%PDF-1.7\nbytes"
    content_hash = hashlib.sha256(content).hexdigest()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/run-artifacts"
        assert request.headers["content-type"] == "application/pdf"
        assert request.headers["x-upload-id"] == "upload_abcdefgh"
        assert request.content == content
        return httpx.Response(
            201,
            json={
                "artifact_ref": "art_abcdefgh",
                "content_hash": content_hash,
                "byte_size": len(content),
                "content_type": "application/pdf",
            },
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    artifact = client.runs.attach_artifact(
        upload_id="upload_abcdefgh",
        file_name="answer.pdf",
        mime_type="application/pdf",
        content=content,
        content_hash=content_hash,
        idempotency_key="artifact-1",
    )

    assert artifact.artifact_ref == "art_abcdefgh"
    client.close()


@pytest.mark.asyncio
async def test_async_run_resources_match_sync_event_surface() -> None:
    stream = b"event: run.event\ndata: {\"type\":\"run.event\",\"event_id\":\"event_aaaaaaaa\",\"run_id\":\"run_33333333333343338333333333333333\",\"sequence\":1,\"phase\":\"completed\",\"status\":\"completed\",\"message_key\":\"run.status.completed\",\"event_cursor\":\"cursor_aaa\"}\n\n"

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/events/stream")
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=stream)

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    messages = [message async for message in client.runs.iter_events(RUN_ID)]

    assert messages[0].status == "completed"
    await client.aclose()


class _StopAwareSyncStream(httpx.SyncByteStream):
    def __init__(self) -> None:
        self.closed = False

    def __iter__(self):
        yield _sse_heartbeat(event_id="heartbeat_aaa", sequence=1)
        raise AssertionError("idle stream was read after caller stop")

    def close(self) -> None:
        self.closed = True


class _IdleSyncStream(httpx.SyncByteStream):
    def __init__(self, read_timeout: float) -> None:
        self.read_timeout = read_timeout
        self.closed = False

    def __iter__(self):
        time.sleep(self.read_timeout + 0.01)
        raise httpx.ReadTimeout("idle stream read timed out")

    def close(self) -> None:
        self.closed = True


class _HeartbeatThenTimeoutSyncStream(httpx.SyncByteStream):
    def __init__(self) -> None:
        self.closed = False

    def __iter__(self):
        yield _sse_heartbeat(event_id="heartbeat_aaa", sequence=1)
        raise httpx.ReadTimeout("heartbeat checkpoint")

    def close(self) -> None:
        self.closed = True


class _StopAwareAsyncStream(httpx.AsyncByteStream):
    def __init__(self) -> None:
        self.closed = False

    async def __aiter__(self):
        yield _sse_heartbeat(event_id="heartbeat_aaa", sequence=1)
        raise AssertionError("idle stream was read after caller stop")

    async def aclose(self) -> None:
        self.closed = True


class _IdleAsyncStream(httpx.AsyncByteStream):
    def __init__(self) -> None:
        self.closed = False

    async def __aiter__(self):
        await asyncio.sleep(60.0)
        yield b""

    async def aclose(self) -> None:
        self.closed = True


def test_sync_iter_events_stops_before_reading_idle_stream() -> None:
    requests: list[httpx.Request] = []
    streams: list[_StopAwareSyncStream] = []
    stop_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        stream = _StopAwareSyncStream()
        streams.append(stream)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=stream,
        )

    def stop() -> bool:
        nonlocal stop_calls
        stop_calls += 1
        return stop_calls > 1

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZenturePollingStoppedError):
        list(client.runs.iter_events(RUN_ID, stop=stop, initial_interval=0.0, max_interval=0.0))

    assert len(requests) == 1
    assert streams[0].closed
    client.close()


@pytest.mark.asyncio
async def test_async_iter_events_stops_before_reading_idle_stream() -> None:
    requests: list[httpx.Request] = []
    streams: list[_StopAwareAsyncStream] = []
    stop_calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        stream = _StopAwareAsyncStream()
        streams.append(stream)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=stream,
        )

    def stop() -> bool:
        nonlocal stop_calls
        stop_calls += 1
        return stop_calls > 1

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZenturePollingStoppedError):
        [
            message
            async for message in client.runs.iter_events(
                RUN_ID, stop=stop, initial_interval=0.0, max_interval=0.0
            )
        ]

    assert len(requests) == 1
    assert streams[0].closed
    await client.aclose()


def test_sync_iter_events_checks_timeout_after_heartbeat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import zenture._resources.runs as runs_module

    clock_values = iter((0.0, 0.0, 0.0, 1.0))
    fake_time = SimpleNamespace(monotonic=lambda: next(clock_values))
    monkeypatch.setattr(runs_module, "time", fake_time)
    streams: list[_StopAwareSyncStream] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        stream = _StopAwareSyncStream()
        streams.append(stream)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=stream,
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZenturePollingTimeoutError):
        list(client.runs.iter_events(RUN_ID, timeout=1.0))

    assert streams[0].closed
    client.close()


@pytest.mark.asyncio
async def test_async_iter_events_checks_timeout_after_heartbeat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import zenture._resources.async_runs as async_runs_module
    import zenture._resources.runs as runs_module

    clock_values = iter((0.0, 0.0, 0.0, 1.0))
    fake_time = SimpleNamespace(monotonic=lambda: next(clock_values))
    monkeypatch.setattr(runs_module, "time", fake_time)
    monkeypatch.setattr(async_runs_module, "time", fake_time)
    streams: list[_StopAwareAsyncStream] = []

    async def handler(_request: httpx.Request) -> httpx.Response:
        stream = _StopAwareAsyncStream()
        streams.append(stream)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=stream,
        )

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZenturePollingTimeoutError):
        [message async for message in client.runs.iter_events(RUN_ID, timeout=1.0)]

    assert streams[0].closed
    await client.aclose()


@pytest.mark.asyncio
async def test_async_iter_events_interrupts_open_idle_stream() -> None:
    streams: list[_IdleAsyncStream] = []

    async def handler(_request: httpx.Request) -> httpx.Response:
        stream = _IdleAsyncStream()
        streams.append(stream)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=stream,
        )

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ZenturePollingTimeoutError):
        [message async for message in client.runs.iter_events(RUN_ID, timeout=0.005)]

    assert streams[0].closed
    await client.aclose()


def test_sync_iter_events_passes_remaining_timeout_to_stream() -> None:
    read_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        read_timeouts.append(request.extensions["timeout"]["read"])
        return _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="completed",
                event_cursor="cursor_aaa",
            )
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    list(client.runs.iter_events(RUN_ID, timeout=5.0))

    assert read_timeouts
    assert 0 < read_timeouts[0] <= 5.0
    client.close()


def test_sync_iter_events_bounds_idle_read_and_closes_stream() -> None:
    streams: list[_IdleSyncStream] = []
    read_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        read_timeout = request.extensions["timeout"]["read"]
        read_timeouts.append(read_timeout)
        stream = _IdleSyncStream(read_timeout)
        streams.append(stream)
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=stream,
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    started = time.monotonic()
    with pytest.raises(ZenturePollingTimeoutError):
        list(
            client.runs.iter_events(
                RUN_ID,
                timeout=0.03,
                initial_interval=0.0,
                max_interval=0.0,
            )
        )
    elapsed = time.monotonic() - started

    assert read_timeouts
    assert read_timeouts[0] <= 0.03
    assert elapsed < 0.2
    assert streams[0].closed
    client.close()


def test_sync_timeout_only_stream_uses_heartbeat_safe_checkpoint() -> None:
    streams: list[_HeartbeatThenTimeoutSyncStream] = []
    read_timeouts: list[float] = []
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        read_timeouts.append(request.extensions["timeout"]["read"])
        if len(requests) == 1:
            stream = _HeartbeatThenTimeoutSyncStream()
            streams.append(stream)
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                stream=stream,
            )
        return _stream_response(
            _sse_event(
                event_id="event_bbb",
                sequence=2,
                status="completed",
                event_cursor="cursor_bbb",
            )
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    messages = list(
        client.runs.iter_events(
            RUN_ID,
            timeout=30.0,
            initial_interval=0.0,
            max_interval=0.0,
        )
    )

    assert [message.event_id for message in messages] == ["heartbeat_aaa", "event_bbb"]
    assert len(requests) == 2
    assert read_timeouts[0] == 15.0
    assert streams[0].closed
    client.close()


def test_sync_timeout_only_stream_reconfigures_at_final_deadline_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import zenture._resources.runs as runs_module

    clock_values = iter((0.0, 0.0, 0.0))

    def monotonic() -> float:
        return next(clock_values, 5.0)

    fake_time = SimpleNamespace(monotonic=monotonic, sleep=lambda _: None)
    monkeypatch.setattr(runs_module, "time", fake_time)
    requests: list[httpx.Request] = []
    read_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        read_timeouts.append(request.extensions["timeout"]["read"])
        if len(requests) == 1:
            return _stream_response(
                _sse_event(
                    event_id="event_aaa",
                    sequence=1,
                    status="running",
                    event_cursor="cursor_aaa",
                )
            )
        return _stream_response(
            _sse_event(
                event_id="event_bbb",
                sequence=2,
                status="completed",
                event_cursor="cursor_bbb",
            )
        )

    client = Zenture(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    messages = list(
        client.runs.iter_events(
            RUN_ID,
            timeout=20.0,
            initial_interval=0.0,
            max_interval=0.0,
        )
    )

    assert [message.event_id for message in messages] == ["event_aaa", "event_bbb"]
    assert read_timeouts == [15.0, 15.0]
    assert requests[1].headers["last-event-id"] == "cursor_aaa"
    client.close()


@pytest.mark.asyncio
async def test_async_iter_events_passes_remaining_timeout_to_stream() -> None:
    read_timeouts: list[float] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        read_timeouts.append(request.extensions["timeout"]["read"])
        return _stream_response(
            _sse_event(
                event_id="event_aaa",
                sequence=1,
                status="completed",
                event_cursor="cursor_aaa",
            )
        )

    client = AsyncZenture(
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    [message async for message in client.runs.iter_events(RUN_ID, timeout=5.0)]

    assert read_timeouts
    assert 0 < read_timeouts[0] <= 5.0
    await client.aclose()


def test_run_event_dedupe_memory_is_bounded_for_long_streams() -> None:
    state = _RunEventStreamState(cursor=None, initial_interval=0.0, max_interval=0.0)

    for sequence in range(1, 2_049):
        state.accept(
            PublicRunEvent.model_validate(
                {
                    "type": "run.event",
                    "event_id": f"event_{sequence}",
                    "run_id": RUN_ID,
                    "sequence": sequence,
                    "phase": "running",
                    "status": "running",
                    "message_key": "run.status.running",
                    "event_cursor": f"cursor_{sequence}",
                }
            )
        )

    assert len(state.seen_event_ids) <= 1_024
