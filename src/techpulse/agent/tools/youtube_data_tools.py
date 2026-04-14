import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.integrations.youtube.exceptions import YouTubeAPIError
from techpulse.integrations.youtube.youtube_data_client import YouTubeDataClient

_HANDLE_PARAM = {
    "type": "string",
    "description": "YouTube channel handle, e.g. '@nickchapsas'.",
}

_CHANNEL_ID_PARAM = {
    "type": "string",
    "description": "YouTube channel ID, e.g. 'UCrkPsvLGln62OMZRO6K-llg'.",
}


class ResolveChannelIdTool(Tool):
    name = "resolve_channel_id"
    description = (
        "Resolves a YouTube channel @handle to its internal channel ID. "
        "Use this to check that a handle is valid before fetching videos from it."
    )
    input_schema = {
        "type": "object",
        "properties": {"channel_handle": _HANDLE_PARAM},
        "required": ["channel_handle"],
        "additionalProperties": False,
    }

    def __init__(self, client: YouTubeDataClient) -> None:
        self._client = client

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        handle: str = tool_input["channel_handle"]
        log = logger.bind(handle=handle)
        log.debug("resolving handle")
        try:
            channel_id = await self._client.get_channel_id(handle)
        except YouTubeAPIError as exc:
            log.warning("resolve error | {}", exc)
            return ToolResult(content=str(exc), is_error=True)
        log.debug("channel_id={}", channel_id)
        return ToolResult(content=json.dumps({"handle": handle, "channel_id": channel_id}))


class GetRecentVideosTool(Tool):
    name = "get_recent_videos"
    description = (
        "Fetches the most recent videos uploaded to a YouTube channel. "
        "Requires a channel ID (use resolve_channel_id first if you only have a handle). "
        "Returns video IDs, titles, and publish dates."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "channel_id": _CHANNEL_ID_PARAM,
            "max_results": {
                "type": "integer",
                "description": "How many recent videos to return (1-50, default 5).",
                "default": 5,
            },
        },
        "required": ["channel_id"],
        "additionalProperties": False,
    }

    def __init__(self, client: YouTubeDataClient) -> None:
        self._client = client

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        channel_id: str = tool_input["channel_id"]
        max_results: int = tool_input.get("max_results", 5)
        log = logger.bind(channel_id=channel_id, max_results=max_results)
        log.debug("fetching recent videos")
        try:
            videos = await self._client.get_recent_videos(channel_id, max_results=max_results)
        except YouTubeAPIError as exc:
            log.warning("fetch error | {}", exc)
            return ToolResult(content=str(exc), is_error=True)
        log.debug("found {}", len(videos))
        payload = {
            "channel_id": channel_id,
            "videos": [
                {
                    "video_id": v.video_id,
                    "title": v.title,
                    "channel_title": v.channel_title,
                    "published_at": v.published_at.isoformat(),
                }
                for v in videos
            ],
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))
