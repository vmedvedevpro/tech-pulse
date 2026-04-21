import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.digest_tool import CheckDigestTool
from techpulse.workers.digest_worker import VideoDigestItem


def _make_item(**overrides) -> VideoDigestItem:
    defaults = {
        "video_id": "vid1",
        "title": "Cool Video",
        "channel_title": "Cool Channel",
        "published_at": datetime(2026, 4, 10, 12, 0, 0),
        "transcript": "Hello world",
        "transcript_language": "en",
    }
    defaults.update(overrides)
    return VideoDigestItem(**defaults)


def _make_tool(yt_returns=None, gh_returns=None) -> tuple[CheckDigestTool, AsyncMock, AsyncMock]:
    yt_worker = AsyncMock()
    yt_worker.collect.return_value = yt_returns if yt_returns is not None else []
    gh_worker = AsyncMock()
    gh_worker.collect.return_value = gh_returns if gh_returns is not None else []
    return CheckDigestTool(yt_worker, gh_worker), yt_worker, gh_worker


class TestCheckDigestTool:
    @pytest.mark.asyncio
    async def test_run_returns_no_new_content_when_both_empty(self):
        tool, _, _ = _make_tool()

        result = await tool.run({})

        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "no_new_content"}

    @pytest.mark.asyncio
    async def test_run_returns_video_list_when_new_videos_found(self):
        tool, _, _ = _make_tool(
            yt_returns=[
                _make_item(video_id="v1", title="First"),
                _make_item(video_id="v2", title="Second", transcript=None, transcript_language=None),
            ]
        )

        result = await tool.run({})

        assert not result.is_error
        payload = json.loads(result.content)
        assert len(payload["new_videos"]) == 2
        assert payload["new_videos"][0]["video_id"] == "v1"
        assert payload["new_videos"][0]["title"] == "First"
        assert payload["new_videos"][1]["transcript"] is None

    @pytest.mark.asyncio
    async def test_run_serializes_published_at_as_iso_format(self):
        dt = datetime(2026, 4, 10, 15, 30, 0)
        tool, _, _ = _make_tool(yt_returns=[_make_item(published_at=dt)])

        result = await tool.run({})

        payload = json.loads(result.content)
        assert payload["new_videos"][0]["published_at"] == dt.isoformat()

    @pytest.mark.asyncio
    async def test_run_calls_both_workers(self):
        tool, yt_worker, gh_worker = _make_tool()

        await tool.run({})

        yt_worker.collect.assert_awaited_once()
        gh_worker.collect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_includes_all_expected_fields_in_video_payload(self):
        tool, _, _ = _make_tool(yt_returns=[_make_item()])

        result = await tool.run({})

        video = json.loads(result.content)["new_videos"][0]
        expected_keys = {"video_id", "title", "channel_title", "published_at", "transcript", "transcript_language"}
        assert set(video.keys()) == expected_keys
