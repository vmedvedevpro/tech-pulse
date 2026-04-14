from youtube_transcript_api import YouTubeTranscriptApi

from techpulse.agent.constants.system_promt import SYSTEM_PROMPT
from techpulse.agent.core.agent import Agent
from techpulse.agent.core.tool_registry import ToolRegistry
from techpulse.agent.tools.youtube_transcript_tools import (
    FetchVideoMetadataTool,
    ListTranscriptsTool,
    YoutubeTranscriptTool,
)
from techpulse.pipeline.integrations.youtube.youtube_api_client import YouTubeTranscriptClient


def create_agent() -> Agent:
    registry = ToolRegistry()
    yt_client = YouTubeTranscriptClient(YouTubeTranscriptApi())
    registry.register(FetchVideoMetadataTool(yt_client))
    registry.register(ListTranscriptsTool(yt_client))
    registry.register(YoutubeTranscriptTool(yt_client))
    return Agent(registry, system=SYSTEM_PROMPT)
