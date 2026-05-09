from telegram import Update
from telegram.ext import ContextTypes

from techpulse.bot.emoji import tg_emoji

_START_TEXT = (
    f"{tg_emoji('logo')} Hi! I'm <b>TechPulse</b> — your personal tech radar.\n\n"
    "I watch YouTube channels and GitHub repos, filter what's worth your time "
    "against your interests, and deliver an AI-curated weekly digest.\n\n"
    f"{tg_emoji('help')} Type /help to see everything I can do."
)

_HELP_TEXT = (
    f"{tg_emoji('logo')} <b>TechPulse — guide</b>\n"
    "Talk to me naturally — I understand intent, not strict commands.\n\n"
    f"{tg_emoji('youtube')} <b>YouTube</b>\n"
    "• Send a video link — I'll pull the transcript and summarize.\n"
    "• <i>«Subscribe to channel @veritasium»</i> — I'll watch their uploads.\n"
    "• <i>«List my channels»</i> · <i>«Remove channel ...»</i>\n\n"
    f"{tg_emoji('github')} <b>GitHub</b>\n"
    "• Send a repo (e.g. <code>microsoft/vscode</code>) — I'll show info and the latest release.\n"
    "• <i>«Watch repo nodejs/node»</i> — track new releases.\n"
    "• <i>«List my repos»</i> · <i>«Remove repo ...»</i>\n\n"
    f"{tg_emoji('interests')} <b>Interests</b>\n"
    "• <i>«My interests: Rust, LLM agents, distributed systems»</i>\n"
    "• <i>«List interests»</i> · <i>«Remove interest ...»</i>\n"
    "Used to rank relevance in your digest.\n\n"
    f"{tg_emoji('digest')} <b>Weekly digest</b>\n"
    "• <i>«Enable weekly digest»</i> — fresh videos and releases delivered automatically.\n"
    "• <i>«Disable digest»</i> · <i>«Digest status»</i>\n"
    "• <i>«What's new?»</i> — on-demand digest right now.\n\n"
    f"{tg_emoji('ai')} <b>How I work</b>\n"
    "I use Claude to analyze content and rank it against your interests. "
    f"{tg_emoji('success')} marks significant releases; minor ones get a one-line note."
)


class StartHandler:
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        assert message is not None
        await message.reply_text(_START_TEXT, parse_mode="HTML")


class HelpHandler:
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        assert message is not None
        await message.reply_text(_HELP_TEXT, parse_mode="HTML")
