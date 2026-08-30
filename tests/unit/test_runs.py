"""Local REST and SSE contract tests for the public Run resources."""

from __future__ import annotations

import httpx
import pytest

from zenture import AsyncZenture, Zenture
from zenture._contract import PublicRunEvent, PublicRunHeartbeat

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


def _run() -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "generation": 1,
        "family": "knowledge",
        "work_type": "answer",
        "profile": "standard",
        "status": "queued",
        "created_at": "2026-08-30T12:00:00Z",
        "updated_at": "2026-08-30T12:00:00Z",
        "queue": {"queue_reason": "queue:admitted", "jobs_ahead": 0},
        "cancellation_requested": False,
    }


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
