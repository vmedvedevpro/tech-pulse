import asyncio
import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient
from techpulse.persistence.repositories.protocols import VideoRepositoryProtocol

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

    def __init__(
            self,
            client: YouTubeTranscriptClient,
            video_repo: VideoRepositoryProtocol,
    ) -> None:
        self._client = client
        self._video_repo = video_repo

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        video_id: str = tool_input["video_id"]
        log = logger.bind(video_id=video_id)

        cached = await self._video_repo.get_metadata(video_id)
        if cached is not None:
            title, channel = cached
            log.debug("metadata cache hit | title={!r} channel={!r}", title, channel)
            payload = {"video_id": video_id, "title": title, "channel": channel}
            return ToolResult(content=json.dumps(payload, ensure_ascii=False))

        log.debug("fetching metadata")
        try:
            meta = await asyncio.to_thread(self._client.fetch_video_metadata, video_id)
        except TranscriptError as exc:
            log.warning("metadata error | {}", exc)
            return ToolResult(content=str(exc), is_error=True)
        log.debug("title={!r} channel={!r}", meta.title, meta.channel)
        await self._video_repo.upsert_metadata(
            video_id=meta.video_id,
            title=meta.title,
            channel_title=meta.channel,
        )
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

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        video_id: str = tool_input["video_id"]
        log = logger.bind(video_id=video_id)
        log.debug("fetching transcript list")

        try:
            transcript_list = await asyncio.to_thread(self._client.get_transcript_metadata, video_id)
        except TranscriptError as exc:
            log.warning("transcript list error | {}", exc)
            return ToolResult(content=str(exc), is_error=True)

        transcripts = [
            {
                "language_code": t.language_code,
                "language": t.language,
                "is_generated": t.is_generated,
            }
            for t in transcript_list
        ]

        log.debug("found {} transcript(s)", len(transcripts))
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

    def __init__(
            self,
            client: YouTubeTranscriptClient,
            video_repo: VideoRepositoryProtocol,
    ) -> None:
        self._client = client
        self._video_repo = video_repo

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        video_id: str = tool_input["video_id"]
        language_code: str = tool_input["language_code"]
        log = logger.bind(video_id=video_id, language=language_code)

        cached = await self._video_repo.get_transcript(video_id)
        if cached is not None and cached[1] == language_code:
            text, lang = cached
            log.debug("transcript cache hit | text_len={}", len(text))
            payload = {
                "video_id": video_id,
                "language_code": lang,
                "duration_seconds": None,
                "text": text,
            }
            return ToolResult(content=json.dumps(payload, ensure_ascii=False))

        log.debug("fetching transcript")
        try:
            transcript = await asyncio.to_thread(self._client.fetch, video_id, language=language_code)
        except TranscriptError as exc:
            log.warning("transcript error | {}", exc)
            return ToolResult(content=str(exc), is_error=True)

        log.debug(
            "duration={}s text_len={}",
            round(transcript.duration),
            len(transcript.text),
        )
        await self._video_repo.set_transcript(
            video_id=transcript.video_id,
            transcript=transcript.text,
            language=transcript.language_code,
        )
        payload = {
            "video_id": transcript.video_id,
            "language_code": transcript.language_code,
            "duration_seconds": round(transcript.duration),
            "text": transcript.text,
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))
