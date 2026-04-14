import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from techpulse.agent.tools.youtube_transcript_tools import ListTranscriptsTool
from techpulse.integrations.youtube.exceptions import TranscriptError


class TestListTranscriptsTool:
    def _make_transcript_entry(self, language_code="en", language="English", is_generated=False):
        return SimpleNamespace(language_code=language_code, language=language, is_generated=is_generated)

    @pytest.mark.asyncio
    async def test_run_returns_json_payload_when_client_succeeds(self):
        # Arrange
        client = MagicMock()
        client.get_transcript_metadata.return_value = [
            self._make_transcript_entry("en", "English", False),
            self._make_transcript_entry("ru", "Russian", True),
        ]
        tool = ListTranscriptsTool(client)

        # Act
        result = await tool.run({"video_id": "abc123"})

        # Assert
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["video_id"] == "abc123"
        assert payload["transcripts"] == [
            {"language_code": "en", "language": "English", "is_generated": False},
            {"language_code": "ru", "language": "Russian", "is_generated": True},
        ]

    @pytest.mark.asyncio
    async def test_run_returns_empty_list_when_no_transcripts_available(self):
        # Arrange
        client = MagicMock()
        client.get_transcript_metadata.return_value = []
        tool = ListTranscriptsTool(client)

        # Act
        result = await tool.run({"video_id": "abc123"})

        # Assert
        assert not result.is_error
        assert json.loads(result.content)["transcripts"] == []

    @pytest.mark.asyncio
    async def test_run_returns_error_result_when_transcript_error_raised(self):
        # Arrange
        client = MagicMock()
        client.get_transcript_metadata.side_effect = TranscriptError("list failed")
        tool = ListTranscriptsTool(client)

        # Act
        result = await tool.run({"video_id": "abc123"})

        # Assert
        assert result.is_error
        assert "list failed" in result.content
