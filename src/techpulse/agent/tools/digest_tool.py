import asyncio
import json
from typing import Any

from loguru import logger

from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.workers.digest_worker import DigestWorker
from techpulse.workers.github_worker import GitHubWorker


class CheckDigestTool(Tool):
    name = "check_digest"
    description = (
        "Checks all subscribed YouTube channels and watched GitHub repositories for new content. "
        "Returns new unseen YouTube videos (with transcripts) and new GitHub releases. "
        "All returned items are marked as seen and will not appear in future checks. "
        "Call this when the user asks to check for new content, get a digest, or see what's new."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, yt_worker: DigestWorker, gh_worker: GitHubWorker) -> None:
        self._yt_worker = yt_worker
        self._gh_worker = gh_worker

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        log = logger.bind(tool="check_digest")
        log.debug("collecting")

        videos, releases = await asyncio.gather(
            self._yt_worker.collect(),
            self._gh_worker.collect(),
        )

        if not videos and not releases:
            log.info("nothing new")
            return ToolResult(content=json.dumps({"status": "no_new_content"}))

        log.info("new_videos={} new_releases={}", len(videos), len(releases))

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
                for item in videos
            ],
            "new_releases": [
                {
                    "repo": item.repo,
                    "tag": item.tag,
                    "name": item.name,
                    "body": item.body,
                    "published_at": item.published_at.isoformat(),
                    "url": item.url,
                }
                for item in releases
            ],
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))
