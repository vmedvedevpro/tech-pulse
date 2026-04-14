import asyncio
import time
from contextlib import suppress

from loguru import logger
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.events import TextDelta
from techpulse.bootstrap import create_agent
from techpulse.config import settings
from techpulse.logging import setup_logging
from techpulse.persistence.channel_repository import ChannelRepository
from techpulse.persistence.redis_client import create_redis
from techpulse.persistence.video_repository import VideoRepository

_DRAFT_INTERVAL = 0.2  # minimum seconds between draft updates
_CHECK_TRIGGER = "Check my subscribed channels for new videos and write a digest."


class BotApp:
    def __init__(self) -> None:
        self._channel_repository: ChannelRepository | None = None
        self._video_repository: VideoRepository | None = None
        self._agents: dict[int, Agent] = {}

    async def initialize(self) -> None:
        redis = await create_redis(settings.redis_url)
        self._channel_repository = ChannelRepository(redis)
        self._video_repository = VideoRepository(redis)
        logger.info("redis connected")

    def _get_agent(self, user_id: int) -> Agent:
        if user_id not in self._agents:
            logger.info("creating agent | user_id={}", user_id)
            self._agents[user_id] = create_agent(
                user_id, self._channel_repository, self._video_repository
            )
            logger.info("agent created | user_id={}", user_id)
        return self._agents[user_id]

    async def _stream_agent_response(
            self,
            user_id: int,
            username: str,
            chat_id: int,
            text: str,
            update: Update,
    ) -> None:
        with logger.contextualize(user_id=user_id, username=username, chat_id=chat_id):
            agent = self._get_agent(user_id)
            bot = update.get_bot()
            draft_id = int(time.time() * 1000) & 0x7FFFFFFF or 1

            async def keep_typing() -> None:
                with suppress(TelegramError, asyncio.CancelledError):
                    while True:
                        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                        await asyncio.sleep(4.0)

            typing_task = asyncio.create_task(keep_typing())

            buffer = ""
            last_pushed = ""
            last_push_at = 0.0

            async def push_draft(draft_text: str) -> None:
                with suppress(TelegramError):
                    await bot.send_message_draft(
                        chat_id=chat_id,
                        draft_id=draft_id,
                        text=draft_text,
                        parse_mode="HTML",
                    )

            try:
                async for event in agent.stream_chat(text):
                    if not isinstance(event, TextDelta):
                        continue
                    buffer += event.text

                    now = asyncio.get_running_loop().time()
                    if buffer.strip() and buffer != last_pushed and (
                            now - last_push_at >= _DRAFT_INTERVAL
                    ):
                        await push_draft(buffer)
                        last_pushed = buffer
                        last_push_at = now

                final = buffer.strip() or "(no response)"
                await update.effective_message.reply_text(final, parse_mode="HTML")

            except Exception as exc:
                logger.exception("agent error | {}", exc)
                await update.effective_message.reply_text(
                    "An error occurred while processing your message."
                )
            finally:
                typing_task.cancel()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return

        user = update.effective_user
        user_id = user.id if user else None
        username = user.username if user else "?"

        if user_id is None:
            logger.warning("message without user_id, skipping")
            return

        logger.info("incoming message | user_id={} len={}", user_id, len(update.message.text))
        await self._stream_agent_response(
            user_id, username, update.effective_chat.id, update.message.text, update
        )

    async def handle_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = user.id if user else None
        username = user.username if user else "?"

        if user_id is None:
            logger.warning("check command without user_id, skipping")
            return

        logger.info("check command | user_id={}", user_id)
        await self._stream_agent_response(
            user_id, username, update.effective_chat.id, _CHECK_TRIGGER, update
        )


def main() -> None:
    setup_logging(settings.log_level)
    logger.info("starting bot")

    bot_app = BotApp()

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(lambda _: bot_app.initialize())
        .build()
    )
    app.add_handler(CommandHandler("check", bot_app.handle_check))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_app.handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
