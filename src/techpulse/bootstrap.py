from youtube_transcript_api import YouTubeTranscriptApi

from techpulse.agent.core.agent import Agent
from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.agent.system_prompt import SYSTEM_PROMPT
from techpulse.agent.tools.channel_tools import AddChannelTool, ListChannelsTool, RemoveChannelTool
from techpulse.agent.tools.youtube_transcript_tools import (
    FetchVideoMetadataTool,
    ListTranscriptsTool,
    YoutubeTranscriptTool,
)
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient
from techpulse.persistence.channel_repository import ChannelRepository


def create_agent(user_id: int, channel_repository: ChannelRepository) -> Agent:
    registry = ToolRegistry()

    yt_client = YouTubeTranscriptClient(YouTubeTranscriptApi())
    registry.register(FetchVideoMetadataTool(yt_client))
    registry.register(ListTranscriptsTool(yt_client))
    registry.register(YoutubeTranscriptTool(yt_client))

    registry.register(AddChannelTool(channel_repository, user_id))
    registry.register(ListChannelsTool(channel_repository, user_id))
    registry.register(RemoveChannelTool(channel_repository, user_id))

    return Agent(registry, system=SYSTEM_PROMPT)
