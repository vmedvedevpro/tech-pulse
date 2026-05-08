import asyncio
import time
from contextlib import suppress

from loguru import logger
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from techpulse.agent.core.events import TextDelta
from techpulse.bot.agent_registry import AgentRegistry

_DRAFT_INTERVAL = 0.2


class ChatHandler:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        user = update.effective_user
        assert user is not None
        logger.info("incoming message | user_id={} len={}", user.id, len(update.message.text))
        await self.stream(user.id, user.username or "?", update.message.chat_id, update.message.text, update)

    async def stream(
            self,
            user_id: int,
            username: str,
            chat_id: int,
            text: str,
            update: Update,
    ) -> None:
        with logger.contextualize(user_id=user_id, username=username, chat_id=chat_id):
            agent = self._registry.get(user_id)
            bot = update.get_bot()
            draft_id = int(time.time() * 1000) & 0x7FFFFFFF or 1

            async def keep_typing() -> None:
                with suppress(TelegramError, asyncio.CancelledError):
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

            final: str
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
            except Exception as exc:
                logger.exception("agent error | {}", exc)
                final = "An error occurred while processing your message."
            finally:
                typing_task.cancel()
                with suppress(asyncio.CancelledError):
                    await typing_task

            message = update.effective_message
            assert message is not None
            await message.reply_text(final, parse_mode="HTML")
