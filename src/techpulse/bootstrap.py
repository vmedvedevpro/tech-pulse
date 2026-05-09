import asyncio
import atexit
import base64
import os
import tempfile
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from telegram import Bot
from telegram.ext import Application, BaseHandler

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.agent.system_prompt import SYSTEM_PROMPT
from techpulse.agent.tools.channel_tools import AddChannelTool, ListChannelsTool, RemoveChannelTool
from techpulse.agent.tools.digest_subscription_tools import (
    GetWeeklyDigestStatusTool,
    SubscribeWeeklyDigestTool,
    UnsubscribeWeeklyDigestTool,
)
from techpulse.agent.tools.digest_tool import CheckDigestTool
from techpulse.agent.tools.github_tools import GetLatestReleaseTool, GetRepoInfoTool
from techpulse.agent.tools.interests_tools import AddInterestTool, ListInterestsTool, RemoveInterestTool
from techpulse.agent.tools.repo_tools import AddRepoTool, ListReposTool, RemoveRepoTool
from techpulse.agent.tools.youtube_data_tools import GetRecentVideosTool, ResolveChannelIdTool
from techpulse.agent.tools.youtube_transcript_tools import (
    FetchVideoMetadataTool,
    ListTranscriptsTool,
    YoutubeTranscriptTool,
)
from techpulse.bot.agent_registry import AgentRegistry
from techpulse.config import Settings
from techpulse.integrations.github.github_client import GitHubClient
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient
from techpulse.integrations.youtube.youtube_data_client import YouTubeDataClient
from techpulse.persistence.repositories.channel_repository import ChannelRepository
from techpulse.persistence.repositories.digest_subscription_repository import DigestSubscriptionRepository
from techpulse.persistence.repositories.protocols import (
    ChannelRepositoryProtocol,
    DigestSubscriptionRepositoryProtocol,
    InterestsRepositoryProtocol,
    RepoRepositoryProtocol,
    SeenItemsRepositoryProtocol,
    VideoRepositoryProtocol,
)
from techpulse.persistence.repositories.release_repository import ReleaseRepository
from techpulse.persistence.repositories.repo_repository import RepoRepository
from techpulse.persistence.repositories.seen_video_repository import SeenVideoRepository
from techpulse.persistence.repositories.user_interests_repository import InterestsRepository
from techpulse.persistence.repositories.video_repository import VideoRepository
from techpulse.workers.digest_scheduler import DigestScheduler
from techpulse.workers.digest_worker import DigestWorker
from techpulse.workers.github_worker import GitHubWorker


@dataclass(frozen=True, slots=True)
class Repositories:
    channel: ChannelRepositoryProtocol
    seen_video: SeenItemsRepositoryProtocol
    video: VideoRepositoryProtocol
    interests: InterestsRepositoryProtocol
    repo: RepoRepositoryProtocol
    release: SeenItemsRepositoryProtocol
    digest_subscription: DigestSubscriptionRepositoryProtocol

    @classmethod
    def from_session_factory(cls, sf: async_sessionmaker[AsyncSession]) -> "Repositories":
        return cls(
            channel=ChannelRepository(sf),
            seen_video=SeenVideoRepository(sf),
            video=VideoRepository(sf),
            interests=InterestsRepository(sf),
            repo=RepoRepository(sf),
            release=ReleaseRepository(sf),
            digest_subscription=DigestSubscriptionRepository(sf),
        )


def _resolve_cookie_file(settings: Settings) -> str | None:
    if not settings.yt_cookies_b64:
        return None
    data = base64.b64decode(settings.yt_cookies_b64)
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='wb')
    f.write(data)
    f.close()
    atexit.register(os.unlink, f.name)
    return f.name


def create_agent(user_id: int, repos: Repositories, settings: Settings, cookie_file: str | None = None) -> Agent:
    registry = ToolRegistry()

    yt_transcript_client = YouTubeTranscriptClient(cookie_file=cookie_file)
    registry.register(FetchVideoMetadataTool(yt_transcript_client))
    registry.register(ListTranscriptsTool(yt_transcript_client))
    registry.register(YoutubeTranscriptTool(yt_transcript_client))

    yt_data_client = YouTubeDataClient(api_key=settings.youtube_api_key, base_url=settings.youtube_api_base_url)
    registry.register(ResolveChannelIdTool(yt_data_client))
    registry.register(GetRecentVideosTool(yt_data_client))

    registry.register(AddChannelTool(repos.channel, user_id))
    registry.register(ListChannelsTool(repos.channel, user_id))
    registry.register(RemoveChannelTool(repos.channel, user_id))

    registry.register(AddInterestTool(repos.interests, user_id))
    registry.register(ListInterestsTool(repos.interests, user_id))
    registry.register(RemoveInterestTool(repos.interests, user_id))

    github_client = GitHubClient(token=settings.github_token)
    registry.register(GetRepoInfoTool(github_client))
    registry.register(GetLatestReleaseTool(github_client))

    registry.register(AddRepoTool(repos.repo, user_id))
    registry.register(ListReposTool(repos.repo, user_id))
    registry.register(RemoveRepoTool(repos.repo, user_id))

    yt_worker = DigestWorker(
        yt_data=yt_data_client,
        yt_transcript=yt_transcript_client,
        channel_repo=repos.channel,
        seen_video_repo=repos.seen_video,
        video_repo=repos.video,
        user_id=user_id,
    )
    gh_worker = GitHubWorker(
        github=github_client,
        repo_repo=repos.repo,
        release_repo=repos.release,
        user_id=user_id,
    )
    registry.register(CheckDigestTool(yt_worker, gh_worker))

    registry.register(SubscribeWeeklyDigestTool(repos.digest_subscription, user_id))
    registry.register(UnsubscribeWeeklyDigestTool(repos.digest_subscription, user_id))
    registry.register(GetWeeklyDigestStatusTool(repos.digest_subscription, user_id))

    return Agent(
        registry,
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        system=SYSTEM_PROMPT,
        user_context_loader=_make_user_context_loader(user_id, repos),
    )


def _make_user_context_loader(
        user_id: int,
        repos: Repositories,
) -> Callable[[], Awaitable[str]]:
    async def load() -> str:
        interests, channels, watched_repos, digest_subscribed = await asyncio.gather(
            repos.interests.get_interests(user_id),
            repos.channel.get_subscriptions(user_id),
            repos.repo.get_repos(user_id),
            repos.digest_subscription.is_subscribed(user_id),
        )
        interests_line = ", ".join(interests) if interests else "(none)"
        channels_line = f"{len(channels)} subscribed" if channels else "(none)"
        repos_line = f"{len(watched_repos)} watched" if watched_repos else "(none)"
        digest_line = "enabled" if digest_subscribed else "disabled"
        return (
            "<user_metadata>\n"
            f"Interests: {interests_line}\n"
            f"YouTube channels: {channels_line}\n"
            f"GitHub repos: {repos_line}\n"
            f"Weekly digest: {digest_line}\n"
            "</user_metadata>"
        )

    return load


def create_agent_factory(repos: Repositories, settings: Settings) -> Callable[[int], Agent]:
    cookie_file = _resolve_cookie_file(settings)

    def factory(user_id: int) -> Agent:
        return create_agent(user_id, repos, settings, cookie_file=cookie_file)

    return factory


def build_application(
        settings: Settings,
        registry: AgentRegistry,
        agent_factory: Callable[[int], Agent],
        repos: Repositories,
        handlers: Iterable[BaseHandler],
) -> Application:
    scheduler: DigestScheduler | None = None

    async def _post_init(application: Application) -> None:
        nonlocal scheduler
        await registry.start()
        scheduler = _build_scheduler(application.bot, repos.digest_subscription, agent_factory, settings)
        await scheduler.start()

    async def _post_shutdown(_: Application) -> None:
        if scheduler is not None:
            await scheduler.stop()
        await registry.stop()

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    for handler in handlers:
        app.add_handler(handler)
    return app


def _build_scheduler(
        bot: Bot,
        sub_repo: DigestSubscriptionRepositoryProtocol,
        agent_factory: Callable[[int], Agent],
        settings: Settings,
) -> DigestScheduler:
    return DigestScheduler(
        bot=bot,
        sub_repo=sub_repo,
        agent_factory=agent_factory,
        dow=settings.weekly_digest_dow,
        hour=settings.weekly_digest_hour,
        tick_interval=settings.digest_scheduler_interval,
    )
