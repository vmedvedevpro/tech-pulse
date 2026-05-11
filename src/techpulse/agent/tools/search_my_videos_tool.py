import json
from typing import Any

from loguru import logger

from techpulse.agent.tools._time_window import TimeWindowParseError, parse_time_window
from techpulse.agent.tools.base import Tool, ToolResult
from techpulse.embeddings import EmbeddingClient
from techpulse.persistence.repositories.protocols import VideoRepositoryProtocol

_SUMMARY_EXCERPT_CHARS = 280
_DEFAULT_LIMIT = 10
_MAX_LIMIT = 25


class SearchMyVideosTool(Tool):
    name = "search_my_videos"
    strict = False
    description = (
        "Semantic search over YouTube videos the user has previously watched (their `seen_videos`). "
        "Use this when the user asks things like 'what did I watch about X', 'find my videos on Y', "
        "or 'remind me what video talked about Z'. "
        "Ranks results by cosine similarity between the query and each video's stored summary embedding. "
        "Scoped strictly to the asking user — never returns other users' history. "
        "Returns video_id, title, channel, published date, when the user watched it, a summary excerpt, "
        "the YouTube URL, and a `distance` score (lower = closer match)."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural-language description of the topic to find, e.g. 'Rust async runtimes'.",
            },
            "since": {
                "type": "string",
                "description": (
                    "Optional time window restricting results to videos watched on/after this point. "
                    "Accepts relative shorthand ('7d', '2w', '1m') or an ISO date ('2026-05-01'). "
                    "Omit for no time filter."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    f"Max results to return (default {_DEFAULT_LIMIT}). "
                    f"Values above {_MAX_LIMIT} are capped server-side."
                ),
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def __init__(
            self,
            video_repo: VideoRepositoryProtocol,
            embedding_client: EmbeddingClient,
            user_id: int,
    ) -> None:
        self._video_repo = video_repo
        self._embedding_client = embedding_client
        self._user_id = user_id

    async def run(self, tool_input: dict[str, Any]) -> ToolResult:
        query: str = tool_input["query"]
        raw_since = tool_input.get("since")
        limit = min(int(tool_input.get("limit", _DEFAULT_LIMIT)), _MAX_LIMIT)
        log = logger.bind(user_id=self._user_id, query=query, since=raw_since, limit=limit)

        try:
            since = parse_time_window(raw_since)
        except TimeWindowParseError as exc:
            log.warning("invalid since | {}", exc)
            return ToolResult(content=str(exc), is_error=True)

        log.debug("embedding query")
        query_embedding = await self._embedding_client.embed(query, input_type="query")

        log.debug("searching")
        hits = await self._video_repo.search_seen_by_summary_embedding(
            self._user_id, query_embedding, since=since, limit=limit,
        )
        log.debug("found {} hit(s)", len(hits))

        payload = {
            "query": query,
            "count": len(hits),
            "results": [
                {
                    "video_id": hit.video_id,
                    "url": f"https://youtu.be/{hit.video_id}",
                    "title": hit.title,
                    "channel": hit.channel_title,
                    "published_at": hit.published_at.isoformat() if hit.published_at else None,
                    "watched_at": hit.watched_at.isoformat(),
                    "summary_excerpt": _excerpt(hit.summary),
                    "distance": round(hit.distance, 4),
                }
                for hit in hits
            ],
        }
        return ToolResult(content=json.dumps(payload, ensure_ascii=False))


def _excerpt(text: str | None) -> str | None:
    if text is None:
        return None
    if len(text) <= _SUMMARY_EXCERPT_CHARS:
        return text
    return text[:_SUMMARY_EXCERPT_CHARS].rstrip() + "…"
