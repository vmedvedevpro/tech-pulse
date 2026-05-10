import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from techpulse.agent.tools.youtube_transcript_tools import YoutubeTranscriptTool
from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.models import Transcript


def _miss_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_transcript.return_value = None
    return repo


def _stub_summarizer(summary: str | None = "Test summary.") -> AsyncMock:
    summarizer = AsyncMock()
    summarizer.get_or_create.return_value = summary
    return summarizer


class TestYoutubeTranscriptTool:
    @pytest.mark.asyncio
    async def test_run_returns_json_payload_when_client_succeeds(self):
        # Arrange
        client = MagicMock()
        client.fetch.return_value = Transcript(
            video_id="abc123", text="Hello world", language_code="en", duration=42.7
        )
        tool = YoutubeTranscriptTool(client, _miss_repo(), _stub_summarizer())

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
        tool = YoutubeTranscriptTool(client, _miss_repo(), _stub_summarizer())

        # Act
        result = await tool.run({"video_id": "v", "language_code": "en"})

        # Assert
        assert json.loads(result.content)["duration_seconds"] == 99

    @pytest.mark.asyncio
    async def test_run_passes_language_code_to_client_when_called(self):
        # Arrange
        client = MagicMock()
        client.fetch.return_value = Transcript("v", "t", "ru", duration=10.0)
        tool = YoutubeTranscriptTool(client, _miss_repo(), _stub_summarizer())

        # Act
        await tool.run({"video_id": "v", "language_code": "ru"})

        # Assert
        client.fetch.assert_called_once_with("v", language="ru")

    @pytest.mark.asyncio
    async def test_run_returns_error_result_when_transcript_error_raised(self):
        # Arrange
        client = MagicMock()
        client.fetch.side_effect = TranscriptError("no transcript available")
        tool = YoutubeTranscriptTool(client, _miss_repo(), _stub_summarizer())

        # Act
        result = await tool.run({"video_id": "abc123", "language_code": "en"})

        # Assert
        assert result.is_error
        assert "no transcript available" in result.content


class TestYoutubeTranscriptToolCache:
    @pytest.mark.asyncio
    async def test_returns_cached_transcript_when_language_matches(self):
        # Arrange
        client = MagicMock()
        repo = AsyncMock()
        repo.get_transcript.return_value = ("cached text", "en")
        tool = YoutubeTranscriptTool(client, repo, _stub_summarizer())

        # Act
        result = await tool.run({"video_id": "vid", "language_code": "en"})

        # Assert
        payload = json.loads(result.content)
        assert payload["text"] == "cached text"
        assert payload["language_code"] == "en"
        assert payload["duration_seconds"] is None
        client.fetch.assert_not_called()
        repo.set_transcript.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetches_fresh_when_cached_language_does_not_match(self):
        # Arrange
        client = MagicMock()
        client.fetch.return_value = Transcript("vid", "russian text", "ru", duration=20.0)
        repo = AsyncMock()
        repo.get_transcript.return_value = ("english text", "en")
        tool = YoutubeTranscriptTool(client, repo, _stub_summarizer())

        # Act
        result = await tool.run({"video_id": "vid", "language_code": "ru"})

        # Assert
        payload = json.loads(result.content)
        assert payload["text"] == "russian text"
        assert payload["language_code"] == "ru"
        client.fetch.assert_called_once_with("vid", language="ru")

    @pytest.mark.asyncio
    async def test_persists_transcript_after_client_fetch_on_cache_miss(self):
        # Arrange
        client = MagicMock()
        client.fetch.return_value = Transcript("vid", "fresh", "en", duration=10.0)
        repo = AsyncMock()
        repo.get_transcript.return_value = None
        tool = YoutubeTranscriptTool(client, repo, _stub_summarizer())

        # Act
        await tool.run({"video_id": "vid", "language_code": "en"})

        # Assert
        repo.set_transcript.assert_awaited_once_with(
            video_id="vid", transcript="fresh", language="en",
        )

    @pytest.mark.asyncio
    async def test_does_not_persist_when_client_raises_error(self):
        # Arrange
        client = MagicMock()
        client.fetch.side_effect = TranscriptError("nope")
        repo = AsyncMock()
        repo.get_transcript.return_value = None
        tool = YoutubeTranscriptTool(client, repo, _stub_summarizer())

        # Act
        await tool.run({"video_id": "vid", "language_code": "en"})

        # Assert
        repo.set_transcript.assert_not_called()


class TestYoutubeTranscriptToolSummary:
    @pytest.mark.asyncio
    async def test_returns_summary_in_payload_after_fresh_fetch(self):
        client = MagicMock()
        client.fetch.return_value = Transcript("vid", "transcript text", "en", duration=10.0)
        summarizer = _stub_summarizer("Generated TL;DR.")
        tool = YoutubeTranscriptTool(client, _miss_repo(), summarizer)

        result = await tool.run({"video_id": "vid", "language_code": "en"})

        payload = json.loads(result.content)
        assert payload["summary"] == "Generated TL;DR."
        summarizer.get_or_create.assert_awaited_once_with("vid", "transcript text", "en")

    @pytest.mark.asyncio
    async def test_returns_summary_in_payload_on_cache_hit(self):
        client = MagicMock()
        repo = AsyncMock()
        repo.get_transcript.return_value = ("cached text", "en")
        summarizer = _stub_summarizer("Cached-path TL;DR.")
        tool = YoutubeTranscriptTool(client, repo, summarizer)

        result = await tool.run({"video_id": "vid", "language_code": "en"})

        payload = json.loads(result.content)
        assert payload["summary"] == "Cached-path TL;DR."
        summarizer.get_or_create.assert_awaited_once_with("vid", "cached text", "en")
        client.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_summary_is_null_when_summarizer_returns_none(self):
        client = MagicMock()
        client.fetch.return_value = Transcript("vid", "text", "en", duration=5.0)
        tool = YoutubeTranscriptTool(client, _miss_repo(), _stub_summarizer(None))

        result = await tool.run({"video_id": "vid", "language_code": "en"})

        payload = json.loads(result.content)
        assert payload["summary"] is None
