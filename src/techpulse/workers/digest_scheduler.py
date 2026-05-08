import asyncio
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from loguru import logger
from telegram import Bot, LinkPreviewOptions
from telegram.error import TelegramError

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.events import TextDelta
from techpulse.persistence.repositories.protocols import DigestSubscriptionRepositoryProtocol

_AGENT_PROMPT = (
    "It's time for the user's scheduled weekly digest. "
    "Call check_digest now. If status is 'no_new_content', tell the user there is nothing new this week. "
    "Otherwise format the result using the digest format from your system prompt. "
    "Respond in the user's preferred language."
)


def last_due_run_utc(now: datetime, dow: int, hour: int) -> datetime:
    days_since = (now.weekday() - dow) % 7
    candidate = (now - timedelta(days=days_since)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    if candidate > now:
        candidate -= timedelta(days=7)
    return candidate


async def _render_digest(agent: Agent) -> str:
    buffer = ""
    async for event in agent.stream_chat(_AGENT_PROMPT):
        if isinstance(event, TextDelta):
            buffer += event.text
    return buffer.strip()


class DigestScheduler:
    def __init__(
            self,
            bot: Bot,
            sub_repo: DigestSubscriptionRepositoryProtocol,
            agent_factory: Callable[[int], Agent],
            dow: int,
            hour: int,
            tick_interval: float,
    ) -> None:
        self._bot = bot
        self._sub_repo = sub_repo
        self._agent_factory = agent_factory
        self._dow = dow
        self._hour = hour
        self._tick_interval = tick_interval
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="digest-scheduler")
        logger.info("digest scheduler started | dow={} hour={}", self._dow, self._hour)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _loop(self) -> None:
        while True:
            try:
                await self._tick()
            except Exception as exc:
                logger.exception("digest scheduler tick failed | {}", exc)
            await asyncio.sleep(self._tick_interval)

    async def _tick(self) -> None:
        now = datetime.now(timezone.utc)
        threshold = last_due_run_utc(now, self._dow, self._hour)
        if now < threshold:
            return

        due_user_ids = await self._sub_repo.list_due(threshold)
        if not due_user_ids:
            return

        logger.info("dispatching weekly digest | count={}", len(due_user_ids))
        for user_id in due_user_ids:
            await self._dispatch_one(user_id)

    async def _dispatch_one(self, user_id: int) -> None:
        log = logger.bind(user_id=user_id)
        try:
            agent = self._agent_factory(user_id)
            text = await _render_digest(agent)
            if not text:
                log.warning("empty digest output, skipping send")
                return

            await self._bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
            await self._sub_repo.mark_sent(user_id, datetime.now(timezone.utc))
            log.info("weekly digest sent")
        except TelegramError as exc:
            log.warning("telegram delivery failed | {}", exc)
        except Exception as exc:
            log.exception("digest dispatch failed | {}", exc)
