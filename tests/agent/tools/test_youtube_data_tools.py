import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from techpulse.agent.tools.youtube_data_tools import (
    GetRecentVideosTool,
    ResolveChannelIdTool,
)
from techpulse.integrations.youtube.exceptions import YouTubeAPIError
from techpulse.integrations.youtube.models import VideoInfo


class TestResolveChannelIdTool:
    @pytest.mark.asyncio
    async def test_run_returns_channel_id_when_handle_is_valid(self):
        # Arrange
        client = AsyncMock()
        client.get_channel_id.return_value = "UC123abc"
        tool = ResolveChannelIdTool(client)

        # Act
        result = await tool.run({"channel_handle": "@testchannel"})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload == {"handle": "@testchannel", "channel_id": "UC123abc"}

    @pytest.mark.asyncio
    async def test_run_passes_handle_to_client(self):
        # Arrange
        client = AsyncMock()
        client.get_channel_id.return_value = "UC123"
        tool = ResolveChannelIdTool(client)

        # Act
        await tool.run({"channel_handle": "@mychan"})

        # Assert
        client.get_channel_id.assert_awaited_once_with("@mychan")

    @pytest.mark.asyncio
    async def test_run_returns_error_when_api_error_raised(self):
        # Arrange
        client = AsyncMock()
        client.get_channel_id.side_effect = YouTubeAPIError("not found")
        tool = ResolveChannelIdTool(client)

        # Act
        result = await tool.run({"channel_handle": "@invalid"})

        # Assert
        assert result.is_error
        assert "not found" in result.content


def _make_video(**overrides) -> VideoInfo:
    defaults = {
        "video_id": "vid1",
        "title": "Test Video",
        "channel_id": "UC123",
        "channel_title": "Test Channel",
        "published_at": datetime(2026, 4, 10, 12, 0, 0),
        "description": "A test video",
    }
    defaults.update(overrides)
    return VideoInfo(**defaults)


class TestGetRecentVideosTool:
    @pytest.mark.asyncio
    async def test_run_returns_videos_when_client_succeeds(self):
        # Arrange
        client = AsyncMock()
        client.get_recent_videos.return_value = [
            _make_video(video_id="v1", title="First"),
            _make_video(video_id="v2", title="Second"),
        ]
        tool = GetRecentVideosTool(client)

        # Act
        result = await tool.run({"channel_id": "UC123"})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["channel_id"] == "UC123"
        assert len(payload["videos"]) == 2
        assert payload["videos"][0]["video_id"] == "v1"
        assert payload["videos"][1]["title"] == "Second"

    @pytest.mark.asyncio
    async def test_run_uses_default_max_results_when_not_provided(self):
        # Arrange
        client = AsyncMock()
        client.get_recent_videos.return_value = []
        tool = GetRecentVideosTool(client)

        # Act
        await tool.run({"channel_id": "UC123"})

        # Assert
        client.get_recent_videos.assert_awaited_once_with("UC123", max_results=5)

    @pytest.mark.asyncio
    async def test_run_passes_custom_max_results_when_provided(self):
        # Arrange
        client = AsyncMock()
        client.get_recent_videos.return_value = []
        tool = GetRecentVideosTool(client)

        # Act
        await tool.run({"channel_id": "UC123", "max_results": 10})

        # Assert
        client.get_recent_videos.assert_awaited_once_with("UC123", max_results=10)

    @pytest.mark.asyncio
    async def test_run_returns_error_when_api_error_raised(self):
        # Arrange
        client = AsyncMock()
        client.get_recent_videos.side_effect = YouTubeAPIError("quota exceeded")
        tool = GetRecentVideosTool(client)

        # Act
        result = await tool.run({"channel_id": "UC123"})

        # Assert
        assert result.is_error
        assert "quota exceeded" in result.content

    @pytest.mark.asyncio
    async def test_run_serializes_published_at_as_iso_format(self):
        # Arrange
        client = AsyncMock()
        dt = datetime(2026, 4, 10, 15, 30, 0)
        client.get_recent_videos.return_value = [_make_video(published_at=dt)]
        tool = GetRecentVideosTool(client)

        # Act
        result = await tool.run({"channel_id": "UC123"})

        # Assert
        payload = json.loads(result.content)
        assert payload["videos"][0]["published_at"] == dt.isoformat()

    @pytest.mark.asyncio
    async def test_run_returns_empty_list_when_no_videos(self):
        # Arrange
        client = AsyncMock()
        client.get_recent_videos.return_value = []
        tool = GetRecentVideosTool(client)

        # Act
        result = await tool.run({"channel_id": "UC123"})

        # Assert
        payload = json.loads(result.content)
        assert payload == {"channel_id": "UC123", "videos": []}
