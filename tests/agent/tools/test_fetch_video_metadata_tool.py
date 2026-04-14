import json
from unittest.mock import MagicMock

import pytest

from techpulse.agent.tools.youtube_transcript_tools import FetchVideoMetadataTool
from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.models import VideoMetadata


class TestFetchVideoMetadataTool:
    @pytest.mark.asyncio
    async def test_run_returns_json_payload_when_client_succeeds(self):
        # Arrange
        client = MagicMock()
        client.fetch_video_metadata.return_value = VideoMetadata(
            video_id="abc123", title="My Video", channel="Cool Channel"
        )
        tool = FetchVideoMetadataTool(client)

        # Act
        result = await tool.run({"video_id": "abc123"})

        # Assert
        assert not result.is_error
        assert json.loads(result.content) == {
            "video_id": "abc123",
            "title": "My Video",
            "channel": "Cool Channel",
        }

    @pytest.mark.asyncio
    async def test_run_passes_video_id_to_client_when_called(self):
        # Arrange
        client = MagicMock()
        client.fetch_video_metadata.return_value = VideoMetadata("x", "T", "C")
        tool = FetchVideoMetadataTool(client)

        # Act
        await tool.run({"video_id": "xyz"})

        # Assert
        client.fetch_video_metadata.assert_called_once_with("xyz")

    @pytest.mark.asyncio
    async def test_run_returns_error_result_when_transcript_error_raised(self):
        # Arrange
        client = MagicMock()
        client.fetch_video_metadata.side_effect = TranscriptError("fetch failed")
        tool = FetchVideoMetadataTool(client)

        # Act
        result = await tool.run({"video_id": "abc123"})

        # Assert
        assert result.is_error
        assert "fetch failed" in result.content
