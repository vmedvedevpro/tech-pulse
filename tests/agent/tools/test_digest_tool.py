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


class TestCheckDigestTool:
    @pytest.mark.asyncio
    async def test_run_returns_no_new_videos_when_collect_is_empty(self):
        # Arrange
        worker = AsyncMock()
        worker.collect.return_value = []
        tool = CheckDigestTool(worker)

        # Act
        result = await tool.run({})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"status": "no_new_videos"}

    @pytest.mark.asyncio
    async def test_run_returns_video_list_when_new_videos_found(self):
        # Arrange
        worker = AsyncMock()
        worker.collect.return_value = [
            _make_item(video_id="v1", title="First"),
            _make_item(video_id="v2", title="Second", transcript=None, transcript_language=None),
        ]
        tool = CheckDigestTool(worker)

        # Act
        result = await tool.run({})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert len(payload["new_videos"]) == 2
        assert payload["new_videos"][0]["video_id"] == "v1"
        assert payload["new_videos"][0]["title"] == "First"
        assert payload["new_videos"][1]["transcript"] is None

    @pytest.mark.asyncio
    async def test_run_serializes_published_at_as_iso_format(self):
        # Arrange
        worker = AsyncMock()
        dt = datetime(2026, 4, 10, 15, 30, 0)
        worker.collect.return_value = [_make_item(published_at=dt)]
        tool = CheckDigestTool(worker)

        # Act
        result = await tool.run({})

        # Assert
        payload = json.loads(result.content)
        assert payload["new_videos"][0]["published_at"] == dt.isoformat()

    @pytest.mark.asyncio
    async def test_run_calls_worker_collect(self):
        # Arrange
        worker = AsyncMock()
        worker.collect.return_value = []
        tool = CheckDigestTool(worker)

        # Act
        await tool.run({})

        # Assert
        worker.collect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_includes_all_expected_fields_in_video_payload(self):
        # Arrange
        worker = AsyncMock()
        worker.collect.return_value = [_make_item()]
        tool = CheckDigestTool(worker)

        # Act
        result = await tool.run({})

        # Assert
        video = json.loads(result.content)["new_videos"][0]
        expected_keys = {"video_id", "title", "channel_title", "published_at", "transcript", "transcript_language"}
        assert set(video.keys()) == expected_keys
