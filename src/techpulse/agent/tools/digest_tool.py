import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.workers.digest_worker import DigestWorker


class CheckDigestTool(Tool):
    name = "check_digest"
    description = (
        "Checks all subscribed YouTube channels for new videos not seen before. "
        "Fetches their transcripts and returns them so you can write a digest. "
        "Videos are marked as seen and will not appear in future checks. "
        "Call this when the user asks to check for new videos, get a digest, or see what's new from their channels."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, worker: DigestWorker) -> None:
        self._worker = worker

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(tool="check_digest")
        log.debug("collecting")
        items = await self._worker.collect()
        if not items:
            log.info("no new videos")
            return ToolResult(content=json.dumps({"status": "no_new_videos"}))
        log.info("new_videos={}", len(items))
        payload = {
            "new_videos": [
                {
                    "video_id": item.video_id,
                    "title": item.title,
                    "channel_title": item.channel_title,
                    "published_at": item.published_at.isoformat(),
                    "transcript": item.transcript,
                    "transcript_language": item.transcript_language,
                }
                for item in items
            ]
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))
