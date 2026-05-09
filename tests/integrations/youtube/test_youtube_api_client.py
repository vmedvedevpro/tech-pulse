from unittest.mock import MagicMock, patch

import pytest

from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.models import SubtitleTrack, Transcript, VideoMetadata
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient, _parse_vtt

_SAMPLE_VTT = """\
WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000 align:start position:0%
Hello world

00:00:03.000 --> 00:00:06.500 align:start position:0%
This is a test
"""

_DEDUP_VTT = """\
WEBVTT

00:00:01.000 --> 00:00:03.000
Hello

00:00:03.000 --> 00:00:05.000
Hello

00:00:05.000 --> 00:00:08.000
Hello there
"""

_TAGGED_VTT = """\
WEBVTT

00:00:01.000 --> 00:00:04.000
Hello<00:00:02.000><c> world</c>
"""


def _make_ydl_class(info: dict):
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = lambda s: mock_ydl
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = info
    return MagicMock(return_value=mock_ydl)


def _make_urlopen(content: str):
    mock_resp = MagicMock()
    mock_resp.read.return_value = content.encode()
    ctx = MagicMock()
    ctx.__enter__ = lambda s: mock_resp
    ctx.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=ctx)


def _make_client(info=None, vtt_content=None):
    ydl_class = _make_ydl_class(info or {})
    urlopen = _make_urlopen(vtt_content or _SAMPLE_VTT)
    return YouTubeTranscriptClient(ydl_class=ydl_class, urlopen=urlopen)


def _make_ydl_class_failing(fail_times: int, info: dict, error_msg: str = "HTTP Error 429: Too Many Requests"):
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = lambda s: mock_ydl
    mock_ydl.__exit__ = MagicMock(return_value=False)
    call_count = 0

    def extract_info(url, download=False, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= fail_times:
            raise RuntimeError(error_msg)
        return info

    mock_ydl.extract_info.side_effect = extract_info
    return MagicMock(return_value=mock_ydl)


class TestExtractInfoRetry:
    _INFO = {"title": "Test", "channel": "Chan"}

    def test_retries_on_429_and_succeeds(self):
        ydl_class = _make_ydl_class_failing(1, self._INFO)
        client = YouTubeTranscriptClient(ydl_class=ydl_class)

        with patch("techpulse.integrations.youtube.youtube_api_client.time.sleep") as mock_sleep:
            result = client.fetch_video_metadata("abc123")

        assert result.title == "Test"
        mock_sleep.assert_called_once_with(30)

    def test_uses_increasing_delays_on_repeated_429(self):
        ydl_class = _make_ydl_class_failing(2, self._INFO)
        client = YouTubeTranscriptClient(ydl_class=ydl_class)

        with patch("techpulse.integrations.youtube.youtube_api_client.time.sleep") as mock_sleep:
            client.fetch_video_metadata("abc123")

        assert [c.args[0] for c in mock_sleep.call_args_list] == [30, 60]

    def test_raises_transcript_error_after_max_retries(self):
        ydl_class = _make_ydl_class_failing(4, self._INFO)
        client = YouTubeTranscriptClient(ydl_class=ydl_class)

        with patch("techpulse.integrations.youtube.youtube_api_client.time.sleep"):
            with pytest.raises(TranscriptError, match="abc123"):
                client.fetch_video_metadata("abc123")

    def test_does_not_retry_non_429_errors(self):
        ydl_class = _make_ydl_class_failing(1, self._INFO, error_msg="network error")
        client = YouTubeTranscriptClient(ydl_class=ydl_class)

        with patch("techpulse.integrations.youtube.youtube_api_client.time.sleep") as mock_sleep:
            with pytest.raises(TranscriptError):
                client.fetch_video_metadata("abc123")

        mock_sleep.assert_not_called()


class TestParseVtt:
    def test_returns_text_and_duration_from_valid_vtt(self):
        text, duration = _parse_vtt(_SAMPLE_VTT)
        assert text == "Hello world This is a test"
        assert duration == pytest.approx(6.5)

    def test_deduplicates_consecutive_identical_lines(self):
        text, _ = _parse_vtt(_DEDUP_VTT)
        assert text == "Hello Hello there"

    def test_strips_inline_tags_from_text(self):
        text, _ = _parse_vtt(_TAGGED_VTT)
        assert text == "Hello world"

    def test_duration_is_max_end_timestamp(self):
        _, duration = _parse_vtt(_SAMPLE_VTT)
        assert duration == pytest.approx(6.5)

    def test_returns_empty_string_for_empty_vtt(self):
        text, duration = _parse_vtt("WEBVTT\n")
        assert text == ""
        assert duration == 0.0


class TestFetchVideoMetadata:
    def test_returns_video_metadata_when_info_is_valid(self):
        info = {"title": "My Video", "channel": "Cool Channel", "uploader": "uploader"}
        client = _make_client(info=info)

        result = client.fetch_video_metadata("abc123")

        assert result == VideoMetadata(video_id="abc123", title="My Video", channel="Cool Channel")

    def test_falls_back_to_uploader_when_channel_is_missing(self):
        info = {"title": "My Video", "uploader": "Cool Uploader"}
        client = _make_client(info=info)

        result = client.fetch_video_metadata("abc123")

        assert result.channel == "Cool Uploader"

    def test_raises_transcript_error_when_extract_info_fails(self):
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: mock_ydl
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = RuntimeError("network error")
        ydl_class = MagicMock(return_value=mock_ydl)
        client = YouTubeTranscriptClient(ydl_class=ydl_class)

        with pytest.raises(TranscriptError, match="abc123"):
            client.fetch_video_metadata("abc123")


class TestGetTranscriptMetadata:
    def _make_formats(self, name: str):
        return [{"ext": "vtt", "url": "https://example.com/sub.vtt", "name": name}]

    def test_returns_manual_subtitles_as_not_generated(self):
        info = {"subtitles": {"en": self._make_formats("English")}, "automatic_captions": {}}
        client = _make_client(info=info)

        result = client.get_transcript_metadata("abc123")

        assert result == [SubtitleTrack(language_code="en", language="English", is_generated=False)]

    def test_returns_auto_captions_as_generated(self):
        info = {
            "subtitles": {},
            "automatic_captions": {"en": self._make_formats("English (auto-generated)")},
        }
        client = _make_client(info=info)

        result = client.get_transcript_metadata("abc123")

        assert result == [SubtitleTrack(language_code="en", language="English", is_generated=True)]

    def test_strips_auto_generated_suffix_from_language_name(self):
        info = {
            "subtitles": {},
            "automatic_captions": {"ru": self._make_formats("Russian (auto-generated)")},
        }
        client = _make_client(info=info)

        result = client.get_transcript_metadata("abc123")

        assert result[0].language == "Russian"

    def test_excludes_live_chat_from_auto_captions(self):
        info = {
            "subtitles": {},
            "automatic_captions": {
                "en": self._make_formats("English (auto-generated)"),
                "live_chat": [{"ext": "json3", "url": "https://example.com/chat"}],
            },
        }
        client = _make_client(info=info)

        result = client.get_transcript_metadata("abc123")

        assert all(t.language_code != "live_chat" for t in result)

    def test_sorts_manual_before_auto_generated(self):
        info = {
            "subtitles": {"en": self._make_formats("English")},
            "automatic_captions": {"ru": self._make_formats("Russian (auto-generated)")},
        }
        client = _make_client(info=info)

        result = client.get_transcript_metadata("abc123")

        assert result[0].is_generated is False
        assert result[1].is_generated is True

    def test_raises_transcript_error_when_extract_info_fails(self):
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: mock_ydl
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = RuntimeError("api down")
        ydl_class = MagicMock(return_value=mock_ydl)
        client = YouTubeTranscriptClient(ydl_class=ydl_class)

        with pytest.raises(TranscriptError, match="abc123"):
            client.get_transcript_metadata("abc123")


class TestFetch:
    def _make_formats(self, ext="vtt"):
        return [{"ext": ext, "url": "https://example.com/sub.vtt"}]

    def test_returns_transcript_from_manual_subtitles(self):
        info = {"subtitles": {"en": self._make_formats()}, "automatic_captions": {}}
        client = _make_client(info=info)

        result = client.fetch("abc123", language="en")

        assert isinstance(result, Transcript)
        assert result.video_id == "abc123"
        assert result.language_code == "en"
        assert "Hello world" in result.text

    def test_falls_back_to_auto_captions_when_manual_absent(self):
        info = {
            "subtitles": {},
            "automatic_captions": {"en": self._make_formats()},
        }
        client = _make_client(info=info)

        result = client.fetch("abc123", language="en")

        assert result.language_code == "en"

    def test_uses_english_when_no_language_provided(self):
        info = {"subtitles": {"en": self._make_formats()}, "automatic_captions": {}}
        client = _make_client(info=info)

        result = client.fetch("abc123")

        assert result.language_code == "en"

    def test_prefers_vtt_format_over_other_formats(self):
        formats = [
            {"ext": "json3", "url": "https://example.com/sub.json3"},
            {"ext": "vtt", "url": "https://example.com/sub.vtt"},
        ]
        info = {"subtitles": {"en": formats}, "automatic_captions": {}}
        urlopen = _make_urlopen(_SAMPLE_VTT)
        ydl_class = _make_ydl_class(info)
        client = YouTubeTranscriptClient(ydl_class=ydl_class, urlopen=urlopen)

        client.fetch("abc123", language="en")

        called_url = urlopen.call_args[0][0]
        assert called_url == "https://example.com/sub.vtt"

    def test_raises_transcript_error_when_language_not_found(self):
        info = {"subtitles": {}, "automatic_captions": {}}
        client = _make_client(info=info)

        with pytest.raises(TranscriptError, match="abc123"):
            client.fetch("abc123", language="ru")

    def test_raises_transcript_error_when_download_fails(self):
        info = {"subtitles": {"en": self._make_formats()}, "automatic_captions": {}}
        ydl_class = _make_ydl_class(info)
        urlopen = MagicMock(side_effect=OSError("connection refused"))
        client = YouTubeTranscriptClient(ydl_class=ydl_class, urlopen=urlopen)

        with pytest.raises(TranscriptError, match="abc123"):
            client.fetch("abc123", language="en")

    def test_raises_transcript_error_when_extract_info_fails(self):
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = lambda s: mock_ydl
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = RuntimeError("no transcript")
        ydl_class = MagicMock(return_value=mock_ydl)
        client = YouTubeTranscriptClient(ydl_class=ydl_class)

        with pytest.raises(TranscriptError, match="abc123"):
            client.fetch("abc123")

    def test_duration_parsed_from_vtt_timestamps(self):
        info = {"subtitles": {"en": self._make_formats()}, "automatic_captions": {}}
        client = _make_client(info=info, vtt_content=_SAMPLE_VTT)

        result = client.fetch("abc123", language="en")

        assert result.duration == pytest.approx(6.5)
