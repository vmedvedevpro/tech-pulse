from loguru import logger
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from techpulse.bot.agent_registry import AgentRegistry
from techpulse.bot.handlers.chat import ChatHandler
from techpulse.bot.handlers.commands import StartHandler
from techpulse.config import settings
from techpulse.logging import setup_logging
from techpulse.persistence.database import create_session_factory
from techpulse.persistence.repositories.channel_repository import ChannelRepository
from techpulse.persistence.repositories.release_repository import ReleaseRepository
from techpulse.persistence.repositories.repo_repository import RepoRepository
from techpulse.persistence.repositories.user_interests_repository import InterestsRepository
from techpulse.persistence.repositories.video_repository import VideoRepository


def main() -> None:
    setup_logging(settings.log_level)
    logger.info("starting bot")

    session_factory = create_session_factory(settings.database_url)
    registry = AgentRegistry(
        channel_repository=ChannelRepository(session_factory),
        video_repository=VideoRepository(session_factory),
        interests_repository=InterestsRepository(session_factory),
        repo_repository=RepoRepository(session_factory),
        release_repository=ReleaseRepository(session_factory),
    )

    chat = ChatHandler(registry)
    start = StartHandler()

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(lambda _: registry.start())
        .post_shutdown(lambda _: registry.stop())
        .build()
    )
    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
