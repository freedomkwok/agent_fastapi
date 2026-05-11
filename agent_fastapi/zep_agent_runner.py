from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ZepAgentResult:
    task_id: str | None
    task_status: str | None
    final_text: str | None


class ZepAgentRunner:
    """Keeps one local zep A2A agent warm for this API process."""

    def __init__(self) -> None:
        self._agent: Any | None = None
        self._build_lock = asyncio.Lock()
        self._run_lock = asyncio.Lock()

    async def invoke(
        self,
        *,
        message: str,
        metadata: dict[str, Any] | None = None,
        task_poll_timeout_sec: float = 600.0,
        task_poll_interval_sec: float = 5.0,
    ) -> ZepAgentResult:
        from agents.agent_core.a2a import OrchestrationMode, run_local_a2a_orchestration

        agent = await self._local_agent()
        async with self._run_lock:
            result = await run_local_a2a_orchestration(
                a2a_agent=agent,
                message_text=message,
                mode=OrchestrationMode.HOST_DRIVEN,
                metadata=metadata,
                task_poll_timeout_sec=task_poll_timeout_sec,
                task_poll_interval_sec=task_poll_interval_sec,
            )
        return ZepAgentResult(
            task_id=result.task_id,
            task_status=result.task_status,
            final_text=result.final_text,
        )

    async def _local_agent(self) -> Any:
        if self._agent is not None:
            return self._agent

        async with self._build_lock:
            if self._agent is None:
                from agents.agent_core.a2a import OrchestrationMode
                from agents.zep_agent.registry import build_local_a2a_zep_agent

                self._agent = await asyncio.to_thread(
                    build_local_a2a_zep_agent,
                    mode=OrchestrationMode.HOST_DRIVEN,
                )
            return self._agent


zep_agent_runner = ZepAgentRunner()
