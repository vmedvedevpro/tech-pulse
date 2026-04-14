import asyncio

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from techpulse.agent.core.agent import Agent
from techpulse.bootstrap import create_agent
from techpulse.config import settings
from techpulse.logging import setup_logging
from techpulse.persistence.channel_repository import ChannelRepository
from techpulse.persistence.redis_client import create_redis

_EDIT_INTERVAL = 0.2  # minimum seconds between Telegram message edits


class BotApp:
    def __init__(self) -> None:
        self._channel_repository: ChannelRepository | None = None
        self._agents: dict[int, Agent] = {}

    async def initialize(self) -> None:
        redis = await create_redis(settings.redis_url)
        self._channel_repository = ChannelRepository(redis)
        logger.info("redis connected")

    def _get_agent(self, user_id: int) -> Agent:
        if user_id not in self._agents:
            logger.info("creating agent | user_id={}", user_id)
            self._agents[user_id] = create_agent(user_id, self._channel_repository)
            logger.info("agent created | user_id={}", user_id)
        return self._agents[user_id]

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return

        user = update.effective_user
        chat_id = update.effective_chat.id
        user_id = user.id if user else None
        username = user.username if user else "?"

        if user_id is None:
            logger.warning("message without user_id, skipping")
            return

        with logger.contextualize(user_id=user_id, username=username, chat_id=chat_id):
            logger.info("incoming message | len={}", len(update.message.text))

            agent = self._get_agent(user_id)
            msg = await update.message.reply_text("...")

            buffer = ""
            last_edit_at = asyncio.get_running_loop().time()

            async def edit(text: str) -> None:
                try:
                    await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
                except BadRequest as e:
                    if "can't parse" in str(e).lower():
                        await msg.edit_text(text)  # fallback to plain text
                    # else: content unchanged, skip

            try:
                async for chunk in agent.stream_chat(update.message.text):
                    buffer += chunk
                    now = asyncio.get_running_loop().time()
                    if now - last_edit_at >= _EDIT_INTERVAL and buffer.strip():
                        await edit(buffer)
                        last_edit_at = now

                await edit(buffer) if buffer.strip() else await msg.edit_text("(no response)")

            except Exception as exc:
                logger.exception("agent error | {}", exc)
                await msg.edit_text("An error occurred while processing your message.")


def main() -> None:
    setup_logging()
    logger.info("starting bot")

    bot_app = BotApp()

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(lambda _: bot_app.initialize())
        .build()
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_app.handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
