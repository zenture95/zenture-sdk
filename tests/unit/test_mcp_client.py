"""Contract tests for the opt-in client-side MCP peer surface."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from zenture._contract import (
    ArtifactUploadResponse,
    ListRunEventsResponse,
    ListRunsResponse,
    PublicRunResponse,
)
from zenture._mcp import AsyncMcpClient, McpClient, McpEndpoint, McpRunRead
from zenture.errors import (
    ZentureMCPDependencyError,
    ZentureMCPError,
    ZentureMCPProtocolError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

RUN_ID = "run_33333333333343338333333333333333"
ARTIFACT_REF = "art_33333333333343338333333333333333"


def _run(*, status: str = "completed") -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "generation": 1,
        "family": "knowledge",
        "work_type": "answer",
        "profile": "standard",
        "status": status,
        "created_at": "2026-09-01T12:00:00Z",
        "updated_at": "2026-09-01T12:00:01Z",
        "completed_at": "2026-09-01T12:00:01Z",
        "artifact_refs": [ARTIFACT_REF],
        "event_cursor": "cursor_1",
    }


def _list_runs() -> dict[str, object]:
    return {
        "runs": [
            {
                "run_id": RUN_ID,
                "status": "completed",
                "decision": "ready",
                "profile": "standard",
                "created_at": "2026-09-01T12:00:00Z",
                "updated_at": "2026-09-01T12:00:01Z",
            }
        ],
        "has_more": False,
    }


def _events() -> dict[str, object]:
    return {
        "events": [
            {
                "type": "run.event",
                "event_id": "event_1",
                "run_id": RUN_ID,
                "sequence": 1,
                "phase": "completed",
                "status": "completed",
                "message_key": "run.status.completed",
                "event_cursor": "cursor_1",
            }
        ],
        "has_more": False,
    }


def _tool_result(payload: object, *, is_error: bool = False) -> ToolResult:
    return ToolResult(structured_content=payload, is_error=is_error)


@dataclass
class ToolResult:
    structured_content: object
    is_error: bool = False


class RecordingTransport:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, Mapping[str, object]]] = []

    def list_tools(self) -> object:
        return {
            "tools": [
                {"name": name}
                for name in (
                    "run",
                    "attach_artifact",
                    "list_runs",
                    "get_run",
                    "cancel_run",
                    "record_run_outcome",
                )
            ]
        }

    def call_tool(self, name: str, arguments: Mapping[str, object]) -> object:
        self.calls.append((name, arguments))
        payload = self.responses[name]
        return _tool_result(payload)


class AsyncRecordingTransport:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, Mapping[str, object]]] = []

    async def list_tools(self) -> object:
        return {
            "tools": [
                {"name": name}
                for name in (
                    "run",
                    "attach_artifact",
                    "list_runs",
                    "get_run",
                    "cancel_run",
                    "record_run_outcome",
                )
            ]
        }

    async def call_tool(self, name: str, arguments: Mapping[str, object]) -> object:
        self.calls.append((name, arguments))
        return _tool_result(self.responses[name])


def _responses() -> dict[str, object]:
    return {
        "run": _run(status="queued"),
        "attach_artifact": {
            "artifact_ref": ARTIFACT_REF,
            "content_hash": "a" * 64,
            "byte_size": 4,
            "content_type": "text/plain",
        },
        "list_runs": _list_runs(),
        "get_run": {**_run(), "event_replay": _events()},
        "cancel_run": _run(status="cancelled"),
        "record_run_outcome": _run(),
    }


def test_sync_mcp_peer_maps_all_product_tools_to_canonical_models() -> None:
    transport = RecordingTransport(_responses())
    client = McpClient(transport)

    assert client.list_tools() == (
        "run",
        "attach_artifact",
        "list_runs",
        "get_run",
        "cancel_run",
        "record_run_outcome",
    )
    client.require_product_tools()

    run = client.run(task="Review this answer", artifact={"type": "text", "value": "text"})
    artifact = client.attach_artifact(
        file_name="answer.txt",
        mime_type="text/plain",
        byte_size=4,
        content_hash="a" * 64,
    )
    runs = client.list_runs(limit=1)
    read = client.get_run(RUN_ID, replay_cursor="cursor_0")
    cancelled = client.cancel_run(RUN_ID)
    outcome = client.record_run_outcome(RUN_ID, outcome="used")

    assert isinstance(run, PublicRunResponse)
    assert isinstance(artifact, ArtifactUploadResponse)
    assert isinstance(runs, ListRunsResponse)
    assert isinstance(read, McpRunRead)
    assert isinstance(read.run, PublicRunResponse)
    assert isinstance(read.event_replay, ListRunEventsResponse)
    assert isinstance(cancelled, PublicRunResponse)
    assert isinstance(outcome, PublicRunResponse)
    assert [name for name, _arguments in transport.calls] == [
        "run",
        "attach_artifact",
        "list_runs",
        "get_run",
        "cancel_run",
        "record_run_outcome",
    ]
    assert transport.calls[0][1]["profile"] == "standard"
    assert transport.calls[3][1] == {
        "run_id": RUN_ID,
        "view": "summary",
        "replay_cursor": "cursor_0",
        "replay_limit": 50,
    }


@pytest.mark.asyncio
async def test_async_mcp_peer_preserves_the_same_typed_boundary() -> None:
    transport = AsyncRecordingTransport(_responses())
    client = AsyncMcpClient(transport)

    assert await client.list_tools() == (
        "run",
        "attach_artifact",
        "list_runs",
        "get_run",
        "cancel_run",
        "record_run_outcome",
    )
    await client.require_product_tools()
    run = await client.run(task="Review this answer", artifact={"type": "text", "value": "text"})
    read = await client.get_run(RUN_ID, replay_cursor="cursor_0")
    await client.cancel_run(RUN_ID)

    assert isinstance(run, PublicRunResponse)
    assert isinstance(read, McpRunRead)
    assert isinstance(read.event_replay, ListRunEventsResponse)
    assert [name for name, _arguments in transport.calls] == ["run", "get_run", "cancel_run"]


def test_mcp_error_is_typed_and_does_not_expose_remote_body() -> None:
    transport = RecordingTransport(
        {
            "run": {
                "error": {
                    "code": "forbidden",
                    "http_status": 403,
                    "retryable": False,
                    "next_action": "reauthorize",
                    "reason": "private-body-must-not-escape",
                }
            }
        }
    )

    with pytest.raises(ZentureMCPError) as error:
        McpClient(transport).run(
            task="Review this answer", artifact={"type": "text", "value": "text"}
        )

    assert error.value.code == "forbidden"
    assert error.value.status_code == 403
    assert error.value.next_action == "reauthorize"
    assert "private-body" not in str(error.value)


def test_mcp_payloads_are_bounded_and_reject_sensitive_fields() -> None:
    transport = RecordingTransport(
        {
            "get_run": {**_run(), "user_id": "must-not-cross-boundary"},
        }
    )

    with pytest.raises(ZentureMCPProtocolError):
        McpClient(transport).get_run(RUN_ID)


def test_mcp_endpoint_accepts_canonical_hosts_and_rejects_arbitrary_origins() -> None:
    assert McpEndpoint.from_value("https://mcp.zenture.app").url == "https://mcp.zenture.app/"
    assert McpEndpoint.from_value("https://mcp-int.zenture.app/").url.endswith("/")
    assert McpEndpoint.from_value("http://127.0.0.1:8100").url.endswith(":8100/")

    with pytest.raises(ValueError, match="approved zenture origin"):
        McpEndpoint.from_value("https://untrusted.example/mcp")
    with pytest.raises(ValueError, match="HTTPS"):
        McpEndpoint.from_value("http://mcp.zenture.app")


def test_sync_mcp_arguments_reject_invalid_run_and_unbounded_inputs() -> None:
    transport = RecordingTransport({"get_run": _run()})
    client = McpClient(transport)

    with pytest.raises(ValueError, match="run_id is invalid"):
        client.get_run("not-a-run")
    with pytest.raises(ValueError, match="greater than or equal"):
        client.list_runs(limit=0)
    with pytest.raises(ValueError, match="blank"):
        client.run(task=" ", artifact={"type": "text", "value": "text"})


def test_mcp_adapter_modules_do_not_import_server_or_private_runtime_clients() -> None:
    from pathlib import Path

    root = Path(__file__).parents[2] / "src" / "zenture" / "_mcp"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "zenture_mcp_server" not in source
    assert "redis" not in source.lower()
    assert "supabase" not in source.lower()


@pytest.mark.asyncio
async def test_official_streamable_transport_is_lazy_and_credential_scoped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import zenture._mcp.transport as transport_module

    requested: list[str] = []
    observed: dict[str, object] = {}

    class StreamContext:
        async def __aenter__(self) -> tuple[object, object, None]:
            return object(), object(), None

        async def __aexit__(self, *_exc_info: object) -> None:
            observed["stream_closed"] = True

    class SessionContext:
        def __init__(self, *_streams: object) -> None:
            pass

        async def __aenter__(self) -> SessionContext:
            observed["session_opened"] = True
            return self

        async def __aexit__(self, *_exc_info: object) -> None:
            observed["session_closed"] = True

        async def initialize(self) -> None:
            observed["initialized"] = True

        async def list_tools(self) -> object:
            return {"tools": [{"name": "run"}]}

        async def call_tool(self, name: str, *, arguments: dict[str, object]) -> object:
            return _tool_result({"name": name, "arguments": arguments})

    def import_module(name: str) -> object:
        requested.append(name)
        if name == "mcp":
            return SimpleNamespace(ClientSession=SessionContext)
        if name == "mcp.client.streamable_http":

            def streamablehttp_client(*_args: object, **kwargs: object) -> StreamContext:
                observed["transport_kwargs"] = kwargs
                return StreamContext()

            return SimpleNamespace(streamablehttp_client=streamablehttp_client)
        raise AssertionError(name)

    monkeypatch.setattr(importlib, "import_module", import_module)
    async with transport_module.open_streamable_http_transport(
        "https://mcp.zenture.app",
        bearer_token=lambda: "opaque",
    ) as transport:
        await transport.list_tools()

    assert requested == ["mcp", "mcp.client.streamable_http"]
    assert observed["initialized"] is True
    assert observed["session_closed"] is True
    assert observed["stream_closed"] is True
    assert observed["transport_kwargs"] == {
        "headers": {"Authorization": "Bearer opaque"},
        "timeout": 30.0,
    }


@pytest.mark.asyncio
async def test_official_transport_reports_missing_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import zenture._mcp.transport as transport_module

    def import_module(_name: str) -> object:
        raise ImportError("optional dependency not installed")

    monkeypatch.setattr(importlib, "import_module", import_module)
    with pytest.raises(ZentureMCPDependencyError):
        async with transport_module.open_streamable_http_transport(
            "https://mcp.zenture.app",
            bearer_token="opaque",
        ):
            raise AssertionError("transport should not open")
