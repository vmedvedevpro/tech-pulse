from telegram import Update
from telegram.ext import ContextTypes


class StartHandler:
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        assert message is not None
        await message.reply_text(
            "Hi! I'm TechPulse. Stay on top of your tech world. Track YouTube channels and GitHub repos, set your interests, and get AI-powered digests — right in Telegram."
        )
