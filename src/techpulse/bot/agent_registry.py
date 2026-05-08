import asyncio
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field

from loguru import logger

from techpulse.agent.core.agent import Agent
from techpulse.config import settings


@dataclass
class _AgentEntry:
    agent: Agent
    last_active: float = field(default_factory=time.monotonic)


class AgentRegistry:
    def __init__(self, agent_factory: Callable[[int], Agent]) -> None:
        self._agent_factory = agent_factory
        self._agents: dict[int, _AgentEntry] = {}
        self._sweep_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._sweep_task = asyncio.create_task(self._eviction_loop(), name="agent-eviction")

    async def stop(self) -> None:
        if self._sweep_task:
            self._sweep_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._sweep_task

    async def _eviction_loop(self) -> None:
        while True:
            await asyncio.sleep(settings.agent_sweep_interval)
            self._evict_inactive()

    def _evict_inactive(self) -> None:
        now = time.monotonic()
        stale = [uid for uid, e in self._agents.items() if now - e.last_active > settings.agent_ttl]
        for uid in stale:
            del self._agents[uid]
            logger.info("agent evicted | user_id={}", uid)

    def get(self, user_id: int) -> Agent:
        if user_id not in self._agents:
            logger.info("creating agent | user_id={}", user_id)
            self._agents[user_id] = _AgentEntry(agent=self._agent_factory(user_id))
            logger.info("agent created | user_id={}", user_id)
        entry = self._agents[user_id]
        entry.last_active = time.monotonic()
        return entry.agent
