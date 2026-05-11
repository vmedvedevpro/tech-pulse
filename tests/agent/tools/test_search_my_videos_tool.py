import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.search_my_videos_tool import SearchMyVideosTool
from techpulse.domain.video import VideoSearchHit

_USER_ID = 42
_QUERY_VECTOR = [0.1] * 1024

_HIT_A = VideoSearchHit(
    video_id="abc123",
    title="Rust async runtimes deep dive",
    channel_title="Jon Gjengset",
    published_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    watched_at=datetime(2026, 5, 5, tzinfo=timezone.utc),
    summary="A walkthrough of how tokio's scheduler dispatches tasks.",
    distance=0.12,
)
_HIT_B = VideoSearchHit(
    video_id="def456",
    title=None,
    channel_title=None,
    published_at=None,
    watched_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
    summary=None,
    distance=0.31,
)


def _make_tool(hits: list[VideoSearchHit]) -> tuple[SearchMyVideosTool, AsyncMock, AsyncMock]:
    repo = AsyncMock()
    repo.search_seen_by_summary_embedding.return_value = hits
    embedder = AsyncMock()
    embedder.embed.return_value = _QUERY_VECTOR
    tool = SearchMyVideosTool(repo, embedder, _USER_ID)
    return tool, repo, embedder


class TestSearchMyVideosTool:
    @pytest.mark.asyncio
    async def test_embeds_query_with_query_input_type(self):
        tool, _, embedder = _make_tool([])

        await tool.run({"query": "rust async"})

        embedder.embed.assert_awaited_once_with("rust async", input_type="query")

    @pytest.mark.asyncio
    async def test_passes_user_id_and_query_vector_to_repo(self):
        tool, repo, _ = _make_tool([])

        await tool.run({"query": "rust async"})

        repo.search_seen_by_summary_embedding.assert_awaited_once()
        args, kwargs = repo.search_seen_by_summary_embedding.call_args
        assert args[0] == _USER_ID
        assert args[1] == _QUERY_VECTOR
        assert kwargs["since"] is None
        assert kwargs["limit"] == 10

    @pytest.mark.asyncio
    async def test_parses_relative_since(self):
        tool, repo, _ = _make_tool([])

        await tool.run({"query": "rust", "since": "7d"})

        kwargs = repo.search_seen_by_summary_embedding.call_args.kwargs
        assert kwargs["since"] is not None
        assert kwargs["since"].tzinfo is not None

    @pytest.mark.asyncio
    async def test_caps_limit(self):
        tool, repo, _ = _make_tool([])

        await tool.run({"query": "rust", "limit": 999})

        assert repo.search_seen_by_summary_embedding.call_args.kwargs["limit"] == 25

    @pytest.mark.asyncio
    async def test_invalid_since_returns_error(self):
        tool, repo, embedder = _make_tool([])

        result = await tool.run({"query": "rust", "since": "yesterday"})

        assert result.is_error
        embedder.embed.assert_not_awaited()
        repo.search_seen_by_summary_embedding.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_payload_structure(self):
        tool, _, _ = _make_tool([_HIT_A, _HIT_B])

        result = await tool.run({"query": "rust async"})

        payload = json.loads(result.content)
        assert payload["query"] == "rust async"
        assert payload["count"] == 2
        assert payload["results"][0] == {
            "video_id": "abc123",
            "url": "https://youtu.be/abc123",
            "title": "Rust async runtimes deep dive",
            "channel": "Jon Gjengset",
            "published_at": "2026-04-01T00:00:00+00:00",
            "watched_at": "2026-05-05T00:00:00+00:00",
            "summary_excerpt": "A walkthrough of how tokio's scheduler dispatches tasks.",
            "distance": 0.12,
        }
        assert payload["results"][1]["title"] is None
        assert payload["results"][1]["summary_excerpt"] is None

    @pytest.mark.asyncio
    async def test_empty_results(self):
        tool, _, _ = _make_tool([])

        result = await tool.run({"query": "obscure topic"})

        payload = json.loads(result.content)
        assert payload == {"query": "obscure topic", "count": 0, "results": []}

    @pytest.mark.asyncio
    async def test_long_summary_is_truncated(self):
        long_hit = VideoSearchHit(
            video_id="x",
            title="t",
            channel_title="c",
            published_at=None,
            watched_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            summary="word " * 200,
            distance=0.5,
        )
        tool, _, _ = _make_tool([long_hit])

        result = await tool.run({"query": "q"})

        excerpt = json.loads(result.content)["results"][0]["summary_excerpt"]
        assert excerpt.endswith("…")
        assert len(excerpt) <= 281
