from __future__ import annotations

import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agent_fastapi.main import DEFAULT_GRAPH_ID, app, get_zep_agent_runner
from agent_fastapi.zep_agent_runner import ZepAgentResult


class FakeZepAgentRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def invoke(
        self,
        *,
        message: str,
        metadata: dict[str, Any] | None = None,
        task_poll_timeout_sec: float = 600.0,
        task_poll_interval_sec: float = 5.0,
    ) -> ZepAgentResult:
        self.calls.append(
            {
                "message": message,
                "metadata": metadata,
                "task_poll_timeout_sec": task_poll_timeout_sec,
                "task_poll_interval_sec": task_poll_interval_sec,
            }
        )
        return ZepAgentResult(
            task_id="task-1",
            task_status="completed",
            final_text="answer",
        )


def test_chat_invokes_zep_agent_with_graph_metadata(caplog: pytest.LogCaptureFixture) -> None:
    runner = FakeZepAgentRunner()
    app.dependency_overrides[get_zep_agent_runner] = lambda: runner
    caplog.set_level(logging.INFO, logger="agent_fastapi.requests")
    try:
        client = TestClient(app)
        response = client.post(
            "/chat",
            json={
                "message": "韩立喜欢的人喜欢韩立吗？",
                "graph_id": "mirofish_53c089d117c649c7",
                "graph_backend": "oracle",
                "metadata": {"source": "api-test"},
                "task_poll_timeout_sec": 30,
                "task_poll_interval_sec": 1,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "task-1",
        "task_status": "completed",
        "final_text": "answer",
    }
    assert runner.calls == [
        {
            "message": "韩立喜欢的人喜欢韩立吗？",
            "metadata": {
                "source": "api-test",
                "graph_id": "mirofish_53c089d117c649c7",
                "graph_backend": "oracle",
            },
            "task_poll_timeout_sec": 30,
            "task_poll_interval_sec": 1,
        }
    ]
    logs = "\n".join(record.getMessage() for record in caplog.records)
    assert 'request started: "POST /chat HTTP/1.1"' in logs
    assert '- "POST /chat HTTP/1.1" 200' in logs


def test_chat_rejects_empty_message() -> None:
    client = TestClient(app)

    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_uses_default_graph_id_when_request_omits_it() -> None:
    runner = FakeZepAgentRunner()
    app.dependency_overrides[get_zep_agent_runner] = lambda: runner
    try:
        client = TestClient(app)
        response = client.post("/chat", json={"message": "use the default graph"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert runner.calls[0]["metadata"] == {"graph_id": DEFAULT_GRAPH_ID}
