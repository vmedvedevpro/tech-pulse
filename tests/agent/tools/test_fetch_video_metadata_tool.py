import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from techpulse.agent.tools.youtube_transcript_tools import FetchVideoMetadataTool
from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.models import VideoMetadata


def _miss_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_metadata.return_value = None
    return repo


class TestFetchVideoMetadataTool:
    @pytest.mark.asyncio
    async def test_run_returns_json_payload_when_client_succeeds(self):
        # Arrange
        client = MagicMock()
        client.fetch_video_metadata.return_value = VideoMetadata(
            video_id="abc123", title="My Video", channel="Cool Channel"
        )
        tool = FetchVideoMetadataTool(client, _miss_repo())

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
        tool = FetchVideoMetadataTool(client, _miss_repo())

        # Act
        await tool.run({"video_id": "xyz"})

        # Assert
        client.fetch_video_metadata.assert_called_once_with("xyz")

    @pytest.mark.asyncio
    async def test_run_returns_error_result_when_transcript_error_raised(self):
        # Arrange
        client = MagicMock()
        client.fetch_video_metadata.side_effect = TranscriptError("fetch failed")
        tool = FetchVideoMetadataTool(client, _miss_repo())

        # Act
        result = await tool.run({"video_id": "abc123"})

        # Assert
        assert result.is_error
        assert "fetch failed" in result.content


class TestFetchVideoMetadataToolCache:
    @pytest.mark.asyncio
    async def test_returns_cached_metadata_without_calling_client(self):
        # Arrange
        client = MagicMock()
        repo = AsyncMock()
        repo.get_metadata.return_value = ("Cached Title", "Cached Channel")
        tool = FetchVideoMetadataTool(client, repo)

        # Act
        result = await tool.run({"video_id": "vid"})

        # Assert
        assert json.loads(result.content) == {
            "video_id": "vid",
            "title": "Cached Title",
            "channel": "Cached Channel",
        }
        client.fetch_video_metadata.assert_not_called()
        repo.upsert_metadata.assert_not_called()

    @pytest.mark.asyncio
    async def test_persists_metadata_after_client_fetch_on_cache_miss(self):
        # Arrange
        client = MagicMock()
        client.fetch_video_metadata.return_value = VideoMetadata("vid", "T", "C")
        repo = AsyncMock()
        repo.get_metadata.return_value = None
        tool = FetchVideoMetadataTool(client, repo)

        # Act
        await tool.run({"video_id": "vid"})

        # Assert
        repo.upsert_metadata.assert_awaited_once_with(
            video_id="vid", title="T", channel_title="C",
        )

    @pytest.mark.asyncio
    async def test_does_not_persist_when_client_raises_error(self):
        # Arrange
        client = MagicMock()
        client.fetch_video_metadata.side_effect = TranscriptError("nope")
        repo = AsyncMock()
        repo.get_metadata.return_value = None
        tool = FetchVideoMetadataTool(client, repo)

        # Act
        await tool.run({"video_id": "vid"})

        # Assert
        repo.upsert_metadata.assert_not_called()
