from loguru import logger
from telegram.ext import CommandHandler, MessageHandler, filters

from techpulse.bootstrap import Repositories, build_application, create_agent_factory
from techpulse.bot.agent_registry import AgentRegistry
from techpulse.bot.handlers.chat import ChatHandler
from techpulse.bot.handlers.commands import HelpHandler, StartHandler
from techpulse.bot.localizer import Localizer
from techpulse.config import settings
from techpulse.logging import setup_logging
from techpulse.persistence.database import create_session_factory


def main() -> None:
    setup_logging(settings.log_level)
    logger.info("starting bot")

    repos = Repositories.from_session_factory(create_session_factory(settings.database_url))
    agent_factory = create_agent_factory(repos, settings)
    registry = AgentRegistry(agent_factory)

    localizer = Localizer(api_key=settings.anthropic_api_key, model=settings.localizer_model)
    chat = ChatHandler(registry)
    start = StartHandler(localizer)
    help_ = HelpHandler(localizer)
    handlers = [
        CommandHandler("start", start.handle),
        CommandHandler("help", help_.handle),
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat.handle_message),
    ]

    app = build_application(settings, registry, agent_factory, repos, handlers)
    app.run_polling()


if __name__ == "__main__":
    main()
