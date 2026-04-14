import asyncio

from loguru import logger
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from techpulse.agent.core.agent import Agent
from techpulse.bootstrap import create_agent
from techpulse.config import settings
from techpulse.logging import setup_logging

_EDIT_INTERVAL = 0.2  # minimum seconds between Telegram message edits


class BotApp:
    def __init__(self) -> None:
        self._agents: dict[int, Agent] = {}

    def _get_agent(self, chat_id: int) -> Agent:
        if chat_id not in self._agents:
            self._agents[chat_id] = create_agent()
        return self._agents[chat_id]

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return

        user = update.effective_user
        chat_id = update.effective_chat.id
        user_id = user.id if user else "?"
        username = user.username if user else "?"

        with logger.contextualize(user_id=user_id, username=username, chat_id=chat_id):
            logger.info("incoming message | len={}", len(update.message.text))

            agent = self._get_agent(chat_id)
            msg = await update.message.reply_text("...")

            buffer = ""
            last_edit_at = asyncio.get_running_loop().time()

            try:
                async for chunk in agent.stream_chat(update.message.text):
                    buffer += chunk
                    now = asyncio.get_running_loop().time()
                    if now - last_edit_at >= _EDIT_INTERVAL and buffer.strip():
                        try:
                            await msg.edit_text(buffer)
                        except BadRequest:
                            pass  # content unchanged, skip
                        last_edit_at = now

                if buffer.strip():
                    try:
                        await msg.edit_text(buffer)
                    except BadRequest:
                        pass
                else:
                    await msg.edit_text("(no response)")

            except Exception as exc:
                logger.exception("agent error | {}", exc)
                await msg.edit_text("An error occurred while processing your message.")


def main() -> None:
    setup_logging()
    logger.info("starting bot")
    bot_app = BotApp()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_app.handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
