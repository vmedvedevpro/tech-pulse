import asyncio
import time
from contextlib import suppress
from dataclasses import dataclass, field

from loguru import logger

from techpulse.agent.core.agent import Agent
from techpulse.bootstrap import create_agent
from techpulse.config import settings
from techpulse.persistence.repositories.channel_repository import ChannelRepository
from techpulse.persistence.repositories.release_repository import ReleaseRepository
from techpulse.persistence.repositories.repo_repository import RepoRepository
from techpulse.persistence.repositories.user_interests_repository import InterestsRepository
from techpulse.persistence.repositories.video_repository import VideoRepository


@dataclass
class _AgentEntry:
    agent: Agent
    last_active: float = field(default_factory=time.monotonic)


class AgentRegistry:
    def __init__(
            self,
            channel_repository: ChannelRepository,
            video_repository: VideoRepository,
            interests_repository: InterestsRepository,
            repo_repository: RepoRepository,
            release_repository: ReleaseRepository,
    ) -> None:
        self._channel_repository = channel_repository
        self._video_repository = video_repository
        self._interests_repository = interests_repository
        self._repo_repository = repo_repository
        self._release_repository = release_repository
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

    # noinspection PyTypeChecker
    def get(self, user_id: int) -> Agent:
        if user_id not in self._agents:
            logger.info("creating agent | user_id={}", user_id)
            agent = create_agent(
                user_id,
                self._channel_repository,
                self._video_repository,
                self._interests_repository,
                self._repo_repository,
                self._release_repository,
            )
            self._agents[user_id] = _AgentEntry(agent=agent)
            logger.info("agent created | user_id={}", user_id)
        entry = self._agents[user_id]
        entry.last_active = time.monotonic()
        return entry.agent
