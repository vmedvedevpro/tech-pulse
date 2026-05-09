from datetime import datetime, timezone

import pytest

from tests.persistence.fakes import FakeVideoRepository


@pytest.fixture
def repo():
    return FakeVideoRepository()


class TestUpsertMetadata:
    async def test_get_metadata_returns_none_when_video_unknown(self, repo):
        assert await repo.get_metadata("vid") is None

    async def test_get_metadata_returns_title_and_channel_after_upsert(self, repo):
        await repo.upsert_metadata("vid", title="T", channel_title="C")

        assert await repo.get_metadata("vid") == ("T", "C")

    async def test_get_metadata_returns_none_when_title_missing(self, repo):
        await repo.upsert_metadata("vid", channel_title="C")

        assert await repo.get_metadata("vid") is None

    async def test_get_metadata_returns_none_when_channel_missing(self, repo):
        await repo.upsert_metadata("vid", title="T")

        assert await repo.get_metadata("vid") is None

    async def test_upsert_overwrites_existing_metadata(self, repo):
        await repo.upsert_metadata("vid", title="Old", channel_title="C")
        await repo.upsert_metadata("vid", title="New", channel_title="C")

        assert await repo.get_metadata("vid") == ("New", "C")


class TestTranscript:
    async def test_get_transcript_returns_none_when_no_video_row(self, repo):
        assert await repo.get_transcript("vid") is None

    async def test_get_transcript_returns_none_when_video_has_no_transcript(self, repo):
        await repo.upsert_metadata("vid", title="T", channel_title="C")

        assert await repo.get_transcript("vid") is None

    async def test_set_transcript_then_get_returns_text_and_language(self, repo):
        await repo.set_transcript("vid", "hello world", "en")

        assert await repo.get_transcript("vid") == ("hello world", "en")

    async def test_set_transcript_overwrites_previous(self, repo):
        await repo.set_transcript("vid", "english text", "en")
        await repo.set_transcript("vid", "русский текст", "ru")

        assert await repo.get_transcript("vid") == ("русский текст", "ru")

    async def test_set_transcript_creates_row_when_metadata_missing(self, repo):
        await repo.set_transcript("vid", "hello", "en")

        assert await repo.get_transcript("vid") == ("hello", "en")
        assert await repo.get_metadata("vid") is None

    async def test_set_transcript_preserves_existing_metadata(self, repo):
        await repo.upsert_metadata(
            "vid",
            title="T",
            channel_title="C",
            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        await repo.set_transcript("vid", "hello", "en")

        assert await repo.get_metadata("vid") == ("T", "C")
        assert await repo.get_transcript("vid") == ("hello", "en")


class TestSummary:
    async def test_get_summary_returns_none_when_unknown(self, repo):
        assert await repo.get_summary("vid") is None

    async def test_set_summary_then_get_returns_text(self, repo):
        await repo.set_summary("vid", "tl;dr")

        assert await repo.get_summary("vid") == "tl;dr"

    async def test_set_summary_overwrites_previous(self, repo):
        await repo.set_summary("vid", "first")
        await repo.set_summary("vid", "second")

        assert await repo.get_summary("vid") == "second"

    async def test_set_summary_does_not_clear_transcript(self, repo):
        await repo.set_transcript("vid", "hello", "en")
        await repo.set_summary("vid", "tl;dr")

        assert await repo.get_transcript("vid") == ("hello", "en")
        assert await repo.get_summary("vid") == "tl;dr"
