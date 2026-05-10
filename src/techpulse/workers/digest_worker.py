import asyncio
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from techpulse.integrations.youtube.exceptions import TranscriptError, YouTubeAPIError
from techpulse.integrations.youtube.models import VideoInfo
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient
from techpulse.integrations.youtube.youtube_data_client import YouTubeDataClient
from techpulse.persistence.repositories.protocols import (
    ChannelRepositoryProtocol,
    SeenItemsRepositoryProtocol,
    VideoRepositoryProtocol,
)
from techpulse.workers.video_summarizer import VideoSummarizer


@dataclass
class VideoDigestItem:
    video_id: str
    title: str
    channel_title: str
    published_at: datetime
    transcript: str | None
    transcript_language: str | None
    summary: str | None


class DigestWorker:
    def __init__(
            self,
            yt_data: YouTubeDataClient,
            yt_transcript: YouTubeTranscriptClient,
            channel_repo: ChannelRepositoryProtocol,
            seen_video_repo: SeenItemsRepositoryProtocol,
            video_repo: VideoRepositoryProtocol,
            summarizer: VideoSummarizer,
            user_id: int,
    ) -> None:
        self._yt_data = yt_data
        self._yt_transcript = yt_transcript
        self._channel_repo = channel_repo
        self._seen_video_repo = seen_video_repo
        self._video_repo = video_repo
        self._summarizer = summarizer
        self._user_id = user_id

    async def collect(self, max_per_channel: int = 5) -> list[VideoDigestItem]:
        subscriptions = await self._channel_repo.get_subscriptions(self._user_id)
        if not subscriptions:
            logger.info("no subscriptions | user_id={}", self._user_id)
            return []

        all_videos: list[VideoInfo] = []
        for channel in subscriptions:
            try:
                channel_id = await self._yt_data.get_channel_id(channel)
                videos = await self._yt_data.get_recent_videos(channel_id, max_results=max_per_channel)
                all_videos.extend(videos)
                logger.debug("channel={} fetched={}", channel, len(videos))
            except YouTubeAPIError as exc:
                logger.warning("channel={} error | {}", channel, exc)

        if not all_videos:
            return []

        video_ids = [v.video_id for v in all_videos]
        unseen_ids = set(await self._seen_video_repo.filter_unseen(self._user_id, video_ids))
        new_videos = [v for v in all_videos if v.video_id in unseen_ids]

        logger.info(
            "user_id={} total={} new={}",
            self._user_id, len(all_videos), len(new_videos),
        )

        if not new_videos:
            return []

        items: list[VideoDigestItem] = []
        for video in new_videos:
            await self._video_repo.upsert_metadata(
                video_id=video.video_id,
                title=video.title,
                channel_id=video.channel_id,
                channel_title=video.channel_title,
                published_at=video.published_at,
            )
            transcript_text, lang = await self._get_or_fetch_transcript(video.video_id)
            summary = await self._get_or_create_summary(video.video_id, transcript_text, lang)
            items.append(VideoDigestItem(
                video_id=video.video_id,
                title=video.title,
                channel_title=video.channel_title,
                published_at=video.published_at,
                transcript=transcript_text,
                transcript_language=lang,
                summary=summary,
            ))

        await self._seen_video_repo.mark_many_seen(self._user_id, [v.video_id for v in new_videos])
        return items

    async def _get_or_fetch_transcript(self, video_id: str) -> tuple[str | None, str | None]:
        cached = await self._video_repo.get_transcript(video_id)
        if cached is not None:
            logger.debug("transcript cache hit | video_id={}", video_id)
            return cached

        text, lang = await self._fetch_best_transcript(video_id)
        if text is not None and lang is not None:
            await self._video_repo.set_transcript(video_id, text, lang)
        return text, lang

    async def _get_or_create_summary(
            self,
            video_id: str,
            transcript: str | None,
            language: str | None,
    ) -> str | None:
        if transcript is None or language is None:
            return None
        return await self._summarizer.get_or_create(video_id, transcript, language)

    async def _fetch_best_transcript(self, video_id: str) -> tuple[str | None, str | None]:
        try:
            transcript_list = await asyncio.to_thread(
                self._yt_transcript.get_transcript_metadata, video_id
            )
        except TranscriptError as exc:
            logger.warning("transcript_list failed | video_id={} | {}", video_id, exc)
            return None, None

        candidates = sorted(transcript_list, key=lambda t: (t.is_generated, t.language_code != "en"))
        if not candidates:
            return None, None

        best = candidates[0]
        try:
            transcript = await asyncio.to_thread(
                self._yt_transcript.fetch, video_id, language=best.language_code
            )
            return transcript.text, transcript.language_code
        except TranscriptError as exc:
            logger.warning(
                "transcript_fetch failed | video_id={} lang={} | {}",
                video_id, best.language_code, exc,
            )
            return None, None
