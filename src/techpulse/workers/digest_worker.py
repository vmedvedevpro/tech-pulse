import asyncio
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from techpulse.integrations.youtube.exceptions import TranscriptError, YouTubeAPIError
from techpulse.integrations.youtube.models import VideoInfo
from techpulse.integrations.youtube.youtube_api_client import YouTubeTranscriptClient
from techpulse.integrations.youtube.youtube_data_client import YouTubeDataClient
from techpulse.persistence.channel_repository import ChannelRepository
from techpulse.persistence.video_repository import VideoRepository


@dataclass
class VideoDigestItem:
    video_id: str
    title: str
    channel_title: str
    published_at: datetime
    transcript: str | None
    transcript_language: str | None


class DigestWorker:
    def __init__(
            self,
            yt_data: YouTubeDataClient,
            yt_transcript: YouTubeTranscriptClient,
            channel_repo: ChannelRepository,
            video_repo: VideoRepository,
            user_id: int,
    ) -> None:
        self._yt_data = yt_data
        self._yt_transcript = yt_transcript
        self._channel_repo = channel_repo
        self._video_repo = video_repo
        self._user_id = user_id

    async def collect(self, max_per_channel: int = 5) -> list[VideoDigestItem]:
        subscriptions = await self._channel_repo.get_subscriptions(self._user_id)
        if not subscriptions:
            logger.info("no subscriptions | user_id={}", self._user_id)
            return []

        all_videos: list[VideoInfo] = []
        for channel in subscriptions:
            try:
                channel_id = await self._yt_data.get_channel_id(channel.handle)
                videos = await self._yt_data.get_recent_videos(channel_id, max_results=max_per_channel)
                all_videos.extend(videos)
                logger.debug("channel={} fetched={}", channel.handle, len(videos))
            except YouTubeAPIError as exc:
                logger.warning("channel={} error | {}", channel.handle, exc)

        if not all_videos:
            return []

        video_ids = [v.video_id for v in all_videos]
        unseen_ids = set(await self._video_repo.filter_unseen(self._user_id, video_ids))
        new_videos = [v for v in all_videos if v.video_id in unseen_ids]

        logger.info(
            "user_id={} total={} new={}",
            self._user_id, len(all_videos), len(new_videos),
        )

        if not new_videos:
            return []

        items: list[VideoDigestItem] = []
        for video in new_videos:
            transcript_text, lang = await self._fetch_best_transcript(video.video_id)
            items.append(VideoDigestItem(
                video_id=video.video_id,
                title=video.title,
                channel_title=video.channel_title,
                published_at=video.published_at,
                transcript=transcript_text,
                transcript_language=lang,
            ))

        await self._video_repo.mark_many_seen(self._user_id, [v.video_id for v in new_videos])
        return items

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
