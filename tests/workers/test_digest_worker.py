from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from techpulse.integrations.youtube.exceptions import TranscriptError
from techpulse.integrations.youtube.models import SubtitleTrack, Transcript, VideoInfo
from techpulse.workers.digest_worker import DigestWorker
from tests.persistence.fakes import (
    FakeChannelRepository,
    FakeSeenItemsRepository,
    FakeVideoRepository,
)

_NOW = datetime(2026, 5, 9, tzinfo=timezone.utc)


def _video(video_id: str, title: str = "Title", channel: str = "Cool Channel") -> VideoInfo:
    return VideoInfo(
        video_id=video_id,
        title=title,
        channel_id="UC123",
        channel_title=channel,
        published_at=_NOW,
        description="",
    )


async def _make_worker(
        *,
        user_id: int = 1,
        channels: dict[str, list[VideoInfo]] | None = None,
        transcript_text: str = "transcript text",
        transcript_lang: str = "en",
        seen_video_repo: FakeSeenItemsRepository | None = None,
        video_repo: FakeVideoRepository | None = None,
        summary_text: str | None = "fake summary",
) -> tuple[DigestWorker, AsyncMock, MagicMock, FakeSeenItemsRepository, FakeVideoRepository]:
    yt_data = AsyncMock()
    yt_transcript = MagicMock()

    channels = channels or {}
    yt_data.get_channel_id.side_effect = lambda h: f"channel-id-{h}"

    async def fake_recent(channel_id: str, max_results: int = 5) -> list[VideoInfo]:
        for h, vids in channels.items():
            if channel_id == f"channel-id-{h}":
                return vids
        return []

    yt_data.get_recent_videos.side_effect = fake_recent

    yt_transcript.get_transcript_metadata.return_value = [
        SubtitleTrack(language_code=transcript_lang, language="English", is_generated=False),
    ]
    yt_transcript.fetch.return_value = Transcript(
        video_id="ignored",
        text=transcript_text,
        language_code=transcript_lang,
        duration=10.0,
    )

    channel_repo = FakeChannelRepository()
    for h in channels:
        await channel_repo.subscribe(user_id, h)

    seen_video_repo = seen_video_repo or FakeSeenItemsRepository()
    video_repo = video_repo or FakeVideoRepository()

    summarizer = AsyncMock()
    summarizer.get_or_create.return_value = summary_text

    worker = DigestWorker(
        yt_data=yt_data,
        yt_transcript=yt_transcript,
        channel_repo=channel_repo,
        seen_video_repo=seen_video_repo,
        video_repo=video_repo,
        summarizer=summarizer,
        user_id=user_id,
    )
    return worker, yt_data, yt_transcript, seen_video_repo, video_repo


class TestCollectNoSubscriptions:
    async def test_returns_empty_when_no_subscribed_channels(self):
        worker, *_ = await _make_worker(channels={})

        result = await worker.collect()

        assert result == []


class TestCollectNewVideos:
    async def test_returns_unseen_videos_with_transcript(self):
        worker, *_ = await _make_worker(
            channels={"@chan": [_video("v1")]},
            transcript_text="hello world",
        )

        result = await worker.collect()

        assert len(result) == 1
        assert result[0].video_id == "v1"
        assert result[0].transcript == "hello world"
        assert result[0].transcript_language == "en"

    async def test_marks_new_videos_as_seen(self):
        worker, _, _, seen_repo, _ = await _make_worker(
            channels={"@chan": [_video("v1"), _video("v2")]},
        )

        await worker.collect()

        assert set(await seen_repo.filter_unseen(1, ["v1", "v2", "v3"])) == {"v3"}

    async def test_persists_metadata_for_new_videos(self):
        worker, _, _, _, video_repo = await _make_worker(
            channels={"@chan": [_video("v1", title="My Vid", channel="My Chan")]},
        )

        await worker.collect()

        assert await video_repo.get_metadata("v1") == ("My Vid", "My Chan")

    async def test_persists_transcript_for_new_videos(self):
        worker, _, _, _, video_repo = await _make_worker(
            channels={"@chan": [_video("v1")]},
            transcript_text="hello",
            transcript_lang="en",
        )

        await worker.collect()

        assert await video_repo.get_transcript("v1") == ("hello", "en")


class TestCollectAllSeen:
    async def test_returns_empty_when_all_videos_already_seen(self):
        seen = FakeSeenItemsRepository()
        await seen.mark_many_seen(1, ["v1"])

        worker, _, yt_transcript, *_ = await _make_worker(
            channels={"@chan": [_video("v1")]},
            seen_video_repo=seen,
        )

        result = await worker.collect()

        assert result == []
        yt_transcript.fetch.assert_not_called()


class TestTranscriptCache:
    async def test_uses_cached_transcript_without_calling_ytdlp(self):
        video_repo = FakeVideoRepository()
        await video_repo.set_transcript("v1", "cached text", "en")

        worker, _, yt_transcript, _, _ = await _make_worker(
            channels={"@chan": [_video("v1")]},
            video_repo=video_repo,
        )

        result = await worker.collect()

        assert result[0].transcript == "cached text"
        assert result[0].transcript_language == "en"
        yt_transcript.fetch.assert_not_called()
        yt_transcript.get_transcript_metadata.assert_not_called()

    async def test_fetches_and_persists_when_cache_empty(self):
        video_repo = FakeVideoRepository()

        worker, _, yt_transcript, _, _ = await _make_worker(
            channels={"@chan": [_video("v1")]},
            transcript_text="freshly fetched",
            video_repo=video_repo,
        )

        await worker.collect()

        yt_transcript.fetch.assert_called_once()
        assert await video_repo.get_transcript("v1") == ("freshly fetched", "en")

    async def test_two_users_share_cached_transcript(self):
        shared_video_repo = FakeVideoRepository()

        worker_a, _, yt_a, _, _ = await _make_worker(
            user_id=1,
            channels={"@chan": [_video("v1")]},
            transcript_text="once",
            video_repo=shared_video_repo,
        )
        worker_b, _, yt_b, _, _ = await _make_worker(
            user_id=2,
            channels={"@chan": [_video("v1")]},
            transcript_text="should-not-be-fetched",
            video_repo=shared_video_repo,
        )

        await worker_a.collect()
        await worker_b.collect()

        assert yt_a.fetch.call_count == 1
        yt_b.fetch.assert_not_called()


class TestTranscriptFailure:
    async def test_returns_none_transcript_when_yt_dlp_fails(self):
        worker, _, yt_transcript, _, video_repo = await _make_worker(
            channels={"@chan": [_video("v1")]},
        )
        yt_transcript.get_transcript_metadata.side_effect = TranscriptError("boom")

        result = await worker.collect()

        assert result[0].transcript is None
        assert result[0].transcript_language is None
        assert await video_repo.get_transcript("v1") is None

    async def test_metadata_persisted_even_when_transcript_fails(self):
        worker, _, yt_transcript, _, video_repo = await _make_worker(
            channels={"@chan": [_video("v1", title="T", channel="C")]},
        )
        yt_transcript.get_transcript_metadata.side_effect = TranscriptError("boom")

        await worker.collect()

        assert await video_repo.get_metadata("v1") == ("T", "C")
