from youtube_transcript_api import YouTubeTranscriptApi

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.agent.system_prompt import SYSTEM_PROMPT
from techpulse.agent.tools.channel_tools import AddChannelTool, ListChannelsTool, RemoveChannelTool
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
from techpulse.config import settings
from techpulse.integrations.github.github_client import GitHubClient
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient
from techpulse.integrations.youtube.youtube_data_client import YouTubeDataClient
from techpulse.persistence.channel_repository import ChannelRepository
from techpulse.persistence.release_repository import ReleaseRepository
from techpulse.persistence.repo_repository import RepoRepository
from techpulse.persistence.user_interests_repository import InterestsRepository
from techpulse.persistence.video_repository import VideoRepository
from techpulse.workers.digest_worker import DigestWorker
from techpulse.workers.github_worker import GitHubWorker


def create_agent(
        user_id: int,
        channel_repository: ChannelRepository,
        video_repository: VideoRepository,
        interests_repository: InterestsRepository,
        repo_repository: RepoRepository,
        release_repository: ReleaseRepository,
) -> Agent:
    registry = ToolRegistry()

    yt_transcript_client = YouTubeTranscriptClient(YouTubeTranscriptApi(), oembed_url=settings.youtube_oembed_url)
    registry.register(FetchVideoMetadataTool(yt_transcript_client))
    registry.register(ListTranscriptsTool(yt_transcript_client))
    registry.register(YoutubeTranscriptTool(yt_transcript_client))

    yt_data_client = YouTubeDataClient(api_key=settings.youtube_api_key, base_url=settings.youtube_api_base_url)
    registry.register(ResolveChannelIdTool(yt_data_client))
    registry.register(GetRecentVideosTool(yt_data_client))

    registry.register(AddChannelTool(channel_repository, user_id))
    registry.register(ListChannelsTool(channel_repository, user_id))
    registry.register(RemoveChannelTool(channel_repository, user_id))

    registry.register(AddInterestTool(interests_repository, user_id))
    registry.register(ListInterestsTool(interests_repository, user_id))
    registry.register(RemoveInterestTool(interests_repository, user_id))

    github_client = GitHubClient(token=settings.github_token)
    registry.register(GetRepoInfoTool(github_client))
    registry.register(GetLatestReleaseTool(github_client))

    registry.register(AddRepoTool(repo_repository, user_id))
    registry.register(ListReposTool(repo_repository, user_id))
    registry.register(RemoveRepoTool(repo_repository, user_id))

    yt_worker = DigestWorker(
        yt_data=yt_data_client,
        yt_transcript=yt_transcript_client,
        channel_repo=channel_repository,
        video_repo=video_repository,
        user_id=user_id,
    )
    gh_worker = GitHubWorker(
        github=github_client,
        repo_repo=repo_repository,
        release_repo=release_repository,
        user_id=user_id,
    )
    registry.register(CheckDigestTool(yt_worker, gh_worker))

    return Agent(registry, system=SYSTEM_PROMPT)
