import json
from unittest.mock import MagicMock

import pytest

from techpulse.agent.tools.youtube_transcript_tools import YoutubeTranscriptTool
from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.models import Transcript


class TestYoutubeTranscriptTool:
    @pytest.mark.asyncio
    async def test_run_returns_json_payload_when_client_succeeds(self):
        # Arrange
        client = MagicMock()
        client.fetch.return_value = Transcript(
            video_id="abc123", text="Hello world", language_code="en", duration=42.7
        )
        tool = YoutubeTranscriptTool(client)

        # Act
        result = await tool.run({"video_id": "abc123", "language_code": "en"})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["video_id"] == "abc123"
        assert payload["text"] == "Hello world"
        assert payload["language_code"] == "en"
        assert payload["duration_seconds"] == 43

    @pytest.mark.asyncio
    async def test_run_returns_rounded_duration_when_duration_is_fractional(self):
        # Arrange
        client = MagicMock()
        client.fetch.return_value = Transcript("v", "t", "en", duration=99.4)
        tool = YoutubeTranscriptTool(client)

        # Act
        result = await tool.run({"video_id": "v", "language_code": "en"})

        # Assert
        assert json.loads(result.content)["duration_seconds"] == 99

    @pytest.mark.asyncio
    async def test_run_passes_language_code_to_client_when_called(self):
        # Arrange
        client = MagicMock()
        client.fetch.return_value = Transcript("v", "t", "ru", duration=10.0)
        tool = YoutubeTranscriptTool(client)

        # Act
        await tool.run({"video_id": "v", "language_code": "ru"})

        # Assert
        client.fetch.assert_called_once_with("v", language="ru")

    @pytest.mark.asyncio
    async def test_run_returns_error_result_when_transcript_error_raised(self):
        # Arrange
        client = MagicMock()
        client.fetch.side_effect = TranscriptError("no transcript available")
        tool = YoutubeTranscriptTool(client)

        # Act
        result = await tool.run({"video_id": "abc123", "language_code": "en"})

        # Assert
        assert result.is_error
        assert "no transcript available" in result.content
