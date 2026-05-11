from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.video import SeenVideo, Video, VideoSearchHit


class VideoRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def upsert_metadata(
            self,
            video_id: str,
            title: str | None = None,
            channel_id: str | None = None,
            channel_title: str | None = None,
            published_at: datetime | None = None,
    ) -> None:
        async with self._factory.begin() as session:
            stmt = insert(Video).values(
                video_id=video_id,
                title=title,
                channel_id=channel_id,
                channel_title=channel_title,
                published_at=published_at,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["video_id"],
                set_={
                    "title": stmt.excluded.title,
                    "channel_id": stmt.excluded.channel_id,
                    "channel_title": stmt.excluded.channel_title,
                    "published_at": stmt.excluded.published_at,
                },
            )
            await session.execute(stmt)

    async def get_metadata(self, video_id: str) -> tuple[str, str] | None:
        async with self._factory.begin() as session:
            stmt = select(Video.title, Video.channel_title).where(Video.video_id == video_id)
            row = (await session.execute(stmt)).one_or_none()
            if row is None or row.title is None or row.channel_title is None:
                return None
            return row.title, row.channel_title

    async def get_transcript(self, video_id: str) -> tuple[str, str] | None:
        async with self._factory.begin() as session:
            stmt = select(Video.transcript, Video.transcript_language).where(
                Video.video_id == video_id
            )
            row = (await session.execute(stmt)).one_or_none()
            if row is None or row.transcript is None:
                return None
            return row.transcript, row.transcript_language

    async def set_transcript(
            self,
            video_id: str,
            transcript: str,
            language: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        async with self._factory.begin() as session:
            stmt = insert(Video).values(
                video_id=video_id,
                transcript=transcript,
                transcript_language=language,
                fetched_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["video_id"],
                set_={
                    "transcript": stmt.excluded.transcript,
                    "transcript_language": stmt.excluded.transcript_language,
                    "fetched_at": stmt.excluded.fetched_at,
                },
            )
            await session.execute(stmt)

    async def get_summary(self, video_id: str) -> str | None:
        async with self._factory.begin() as session:
            stmt = select(Video.summary).where(Video.video_id == video_id)
            return (await session.execute(stmt)).scalar_one_or_none()

    async def set_summary(self, video_id: str, summary: str) -> None:
        async with self._factory.begin() as session:
            stmt = insert(Video).values(video_id=video_id, summary=summary)
            stmt = stmt.on_conflict_do_update(
                index_elements=["video_id"],
                set_={"summary": stmt.excluded.summary},
            )
            await session.execute(stmt)

    async def set_summary_embedding(self, video_id: str, embedding: list[float]) -> None:
        async with self._factory.begin() as session:
            stmt = insert(Video).values(video_id=video_id, summary_embedding=embedding)
            stmt = stmt.on_conflict_do_update(
                index_elements=["video_id"],
                set_={"summary_embedding": stmt.excluded.summary_embedding},
            )
            await session.execute(stmt)

    async def search_seen_by_summary_embedding(
            self,
            user_id: int,
            query_embedding: list[float],
            *,
            since: datetime | None,
            limit: int,
    ) -> list[VideoSearchHit]:
        distance = Video.summary_embedding.cosine_distance(query_embedding).label("distance")
        stmt = (
            select(
                Video.video_id,
                Video.title,
                Video.channel_title,
                Video.published_at,
                SeenVideo.created_at.label("watched_at"),
                Video.summary,
                distance,
            )
            .join(SeenVideo, SeenVideo.video_id == Video.video_id)
            .where(
                SeenVideo.user_id == user_id,
                Video.summary_embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(SeenVideo.created_at >= since)

        async with self._factory.begin() as session:
            rows = (await session.execute(stmt)).all()

        return [
            VideoSearchHit(
                video_id=row.video_id,
                title=row.title,
                channel_title=row.channel_title,
                published_at=row.published_at,
                watched_at=row.watched_at,
                summary=row.summary,
                distance=float(row.distance),
            )
            for row in rows
        ]
