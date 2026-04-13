import json
from typing import Any

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.pipeline.integrations.youtube.exceptions import TranscriptError
from techpulse.pipeline.integrations.youtube.youtube_api_client import YouTubeTranscriptClient

_VIDEO_ID_PARAM = {
    "type": "string",
    "description": "YouTube video ID (e.g. 'dQw4w9WgXcQ', not the full URL).",
}


class FetchVideoMetadataTool(Tool):
    name = "fetch_video_metadata"
    description = (
        "Fetches basic metadata for a YouTube video: title and channel name. "
        "Call this first to get the video title before analyzing the transcript."
    )
    input_schema = {
        "type": "object",
        "properties": {"video_id": _VIDEO_ID_PARAM},
        "required": ["video_id"],
        "additionalProperties": False,
    }

    def __init__(self, client: YouTubeTranscriptClient) -> None:
        self._client = client

    def run(self, tool_input: dict[str, Any]) -> ToolResult:
        video_id: str = tool_input["video_id"]
        try:
            meta = self._client.fetch_video_metadata(video_id)
        except TranscriptError as exc:
            return ToolResult(content=str(exc), is_error=True)
        payload = {"video_id": meta.video_id, "title": meta.title, "channel": meta.channel}
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))


class ListTranscriptsTool(Tool):
    name = "list_transcripts"
    description = (
        "Lists all available transcripts for a YouTube video. "
        "Always call this first before fetch_transcript to discover which languages are available "
        "and whether each transcript is manual or auto-generated. "
        "Returns transcripts sorted by preference: manual ones come before auto-generated."
    )
    input_schema = {
        "type": "object",
        "properties": {"video_id": _VIDEO_ID_PARAM},
        "required": ["video_id"],
        "additionalProperties": False,
    }

    def __init__(self, client: YouTubeTranscriptClient) -> None:
        self._client = client

    def run(self, tool_input: dict[str, Any]) -> ToolResult:
        video_id: str = tool_input["video_id"]

        try:
            transcript_list = self._client.get_transcript_metadata(video_id)
        except TranscriptError as exc:
            return ToolResult(content=str(exc), is_error=True)

        transcripts = [
            {
                "language_code": t.language_code,
                "language": t.language,
                "is_generated": t.is_generated,
            }
            for t in transcript_list
        ]

        payload = {"video_id": video_id, "transcripts": transcripts}
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))


class YoutubeTranscriptTool(Tool):
    name = "fetch_transcript"
    description = (
        "Fetches the full transcript of a YouTube video in the specified language. "
        "Always call list_transcripts first to get available languages, "
        "then choose a language_code — prefer manual transcripts (is_generated=false) over auto-generated ones. "
        "Returns transcript text, language code, and duration in seconds."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "video_id": _VIDEO_ID_PARAM,
            "language_code": {
                "type": "string",
                "description": (
                    "Language code from list_transcripts (e.g. 'en', 'ru'). "
                    "Prefer a manual transcript (is_generated=false) when available."
                ),
            },
        },
        "required": ["video_id", "language_code"],
        "additionalProperties": False,
    }

    def __init__(self, client: YouTubeTranscriptClient) -> None:
        self._client = client

    def run(self, tool_input: dict[str, Any]) -> ToolResult:
        video_id: str = tool_input["video_id"]
        language_code: str = tool_input["language_code"]

        try:
            transcript = self._client.fetch(video_id, language=language_code)
        except TranscriptError as exc:
            return ToolResult(content=str(exc), is_error=True)

        payload = {
            "video_id": transcript.video_id,
            "language_code": transcript.language_code,
            "duration_seconds": round(transcript.duration),
            "text": transcript.text,
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))
