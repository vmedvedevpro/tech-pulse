from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes, Application, MessageHandler, filters

from techpulse.bootstrap import create_agent
from techpulse.bot.formatters import format_summary
from techpulse.config import settings
from techpulse.logging import setup_logging

YOUTUBE_RE = r"https?://(?:www\.)?(?:youtube\.com/watch\?(?:\S*&)?v=|youtu\.be/)[\w\-]+"


async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not context.matches:
        return

    url = context.matches[0].group()
    user = update.effective_user
    user_id = user.id if user else "?"
    username = user.username if user else "?"

    with logger.contextualize(user_id=user_id, username=username, url=url):
        logger.info("incoming youtube link")

        await update.message.reply_text("Analyzing...")

        agent, submit_tool = create_agent()
        try:
            await agent.chat(url)
        except Exception as exc:
            logger.exception("agent error | {}", exc)
            await update.message.reply_text("An error occurred while analyzing the video.")
            return

        if submit_tool.last_result is None:
            logger.warning("no summary produced")
            await update.message.reply_text("Agent failed to produce a summary.")
            return

        logger.info("done | title={!r}", submit_tool.last_result.title)
        text = format_summary(submit_tool.last_result)
        await update.message.reply_text(text, parse_mode="HTML")


def main() -> None:
    setup_logging()
    logger.info("starting bot")
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(MessageHandler(filters.Regex(YOUTUBE_RE), handle_youtube_link))
    app.run_polling()


if __name__ == "__main__":
    main()
