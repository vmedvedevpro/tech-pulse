from youtube_transcript_api import YouTubeTranscriptApi

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.agent.system_prompt import SYSTEM_PROMPT
from techpulse.agent.tools.channel_tools import AddChannelTool, ListChannelsTool, RemoveChannelTool
from techpulse.agent.tools.digest_tool import CheckDigestTool
from techpulse.agent.tools.interests_tools import AddInterestTool, ListInterestsTool, RemoveInterestTool
from techpulse.agent.tools.youtube_data_tools import GetRecentVideosTool, ResolveChannelIdTool
from techpulse.agent.tools.youtube_transcript_tools import (
    FetchVideoMetadataTool,
    ListTranscriptsTool,
    YoutubeTranscriptTool,
)
from techpulse.config import settings
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient
from techpulse.integrations.youtube.youtube_data_client import YouTubeDataClient
from techpulse.persistence.channel_repository import ChannelRepository
from techpulse.persistence.user_interests_repository import InterestsRepository
from techpulse.persistence.video_repository import VideoRepository
from techpulse.workers.digest_worker import DigestWorker


def create_agent(
        user_id: int,
        channel_repository: ChannelRepository,
        video_repository: VideoRepository,
        interests_repository: InterestsRepository,
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

    digest_worker = DigestWorker(
        yt_data=yt_data_client,
        yt_transcript=yt_transcript_client,
        channel_repo=channel_repository,
        video_repo=video_repository,
        user_id=user_id,
    )
    registry.register(CheckDigestTool(digest_worker))

    return Agent(registry, system=SYSTEM_PROMPT)
