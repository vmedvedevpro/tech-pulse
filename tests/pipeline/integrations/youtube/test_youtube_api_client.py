import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from techpulse.pipeline.integrations.youtube.exceptions import TranscriptError
from techpulse.pipeline.integrations.youtube.models import Transcript, VideoMetadata
from techpulse.pipeline.integrations.youtube.youtube_api_client import YouTubeTranscriptClient


def _make_client(api=None, urlopen=None):
    return YouTubeTranscriptClient(
        api=api or MagicMock(),
        urlopen=urlopen or MagicMock(),
    )


def _mock_urlopen(data: dict):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(data)
    ctx = MagicMock()
    ctx.__enter__ = lambda s: mock_response
    ctx.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=ctx)


class TestYouTubeTranscriptClient:
    # fetch_video_metadata

    def test_fetch_video_metadata_returns_video_metadata_when_response_is_valid(self):
        # Arrange
        urlopen = _mock_urlopen({"title": "My Video", "author_name": "Cool Channel"})
        client = _make_client(urlopen=urlopen)

        # Act
        result = client.fetch_video_metadata("abc123")

        # Assert
        assert result == VideoMetadata(video_id="abc123", title="My Video", channel="Cool Channel")

    def test_fetch_video_metadata_builds_url_with_video_id_when_called(self):
        # Arrange
        urlopen = _mock_urlopen({"title": "T", "author_name": "C"})
        client = _make_client(urlopen=urlopen)

        # Act
        client.fetch_video_metadata("xyz")

        # Assert
        called_url = urlopen.call_args[0][0]
        assert "xyz" in called_url
        assert "oembed" in called_url

    def test_fetch_video_metadata_raises_transcript_error_when_urlopen_fails(self):
        # Arrange
        urlopen = MagicMock(side_effect=OSError("network error"))
        client = _make_client(urlopen=urlopen)

        # Act / Assert
        with pytest.raises(TranscriptError, match="abc123"):
            client.fetch_video_metadata("abc123")

    def test_fetch_video_metadata_raises_transcript_error_when_json_is_invalid(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.read.return_value = "not-json"
        ctx = MagicMock()
        ctx.__enter__ = lambda s: mock_response
        ctx.__exit__ = MagicMock(return_value=False)
        client = _make_client(urlopen=MagicMock(return_value=ctx))

        # Act / Assert
        with pytest.raises(TranscriptError):
            client.fetch_video_metadata("abc123")

    # get_transcript_metadata

    def test_get_transcript_metadata_returns_api_result_when_api_succeeds(self):
        # Arrange
        api = MagicMock()
        expected = [SimpleNamespace(language_code="en", language="English", is_generated=False)]
        api.list.return_value = expected
        client = _make_client(api=api)

        # Act
        result = client.get_transcript_metadata("abc123")

        # Assert
        assert result is expected
        api.list.assert_called_once_with("abc123")

    def test_get_transcript_metadata_raises_transcript_error_when_api_fails(self):
        # Arrange
        api = MagicMock()
        api.list.side_effect = RuntimeError("api down")
        client = _make_client(api=api)

        # Act / Assert
        with pytest.raises(TranscriptError, match="abc123"):
            client.get_transcript_metadata("abc123")

    # fetch

    def _make_mock_transcript(self, language_code="en", snippets=None):
        if snippets is None:
            snippets = [
                SimpleNamespace(text="Hello", duration=2.5),
                SimpleNamespace(text="world", duration=1.5),
            ]
        return SimpleNamespace(language_code=language_code, snippets=snippets)

    def test_fetch_returns_joined_text_when_multiple_snippets(self):
        # Arrange
        api = MagicMock()
        api.fetch.return_value = self._make_mock_transcript()
        client = _make_client(api=api)

        # Act
        result = client.fetch("abc123")

        # Assert
        assert isinstance(result, Transcript)
        assert result.text == "Hello world"
        assert result.video_id == "abc123"

    def test_fetch_returns_summed_duration_when_multiple_snippets(self):
        # Arrange
        api = MagicMock()
        api.fetch.return_value = self._make_mock_transcript()
        client = _make_client(api=api)

        # Act
        result = client.fetch("abc123")

        # Assert
        assert result.duration == pytest.approx(4.0)

    def test_fetch_returns_language_code_from_api_response(self):
        # Arrange
        api = MagicMock()
        api.fetch.return_value = self._make_mock_transcript(language_code="ru")
        client = _make_client(api=api)

        # Act
        result = client.fetch("abc123", language="ru")

        # Assert
        assert result.language_code == "ru"

    def test_fetch_passes_explicit_language_to_api_when_language_provided(self):
        # Arrange
        api = MagicMock()
        api.fetch.return_value = self._make_mock_transcript(language_code="ru")
        client = _make_client(api=api)

        # Act
        client.fetch("abc123", language="ru")

        # Assert
        api.fetch.assert_called_once_with("abc123", languages=("ru",))

    def test_fetch_uses_english_when_no_language_provided(self):
        # Arrange
        api = MagicMock()
        api.fetch.return_value = self._make_mock_transcript()
        client = _make_client(api=api)

        # Act
        client.fetch("abc123")

        # Assert
        api.fetch.assert_called_once_with("abc123", languages=("en",))

    def test_fetch_raises_transcript_error_when_api_fails(self):
        # Arrange
        api = MagicMock()
        api.fetch.side_effect = RuntimeError("no transcript")
        client = _make_client(api=api)

        # Act / Assert
        with pytest.raises(TranscriptError, match="abc123"):
            client.fetch("abc123")

    def test_fetch_returns_snippet_text_when_single_snippet(self):
        # Arrange
        api = MagicMock()
        api.fetch.return_value = self._make_mock_transcript(
            snippets=[SimpleNamespace(text="Only this", duration=10.0)]
        )
        client = _make_client(api=api)

        # Act
        result = client.fetch("abc123")

        # Assert
        assert result.text == "Only this"
        assert result.duration == pytest.approx(10.0)
