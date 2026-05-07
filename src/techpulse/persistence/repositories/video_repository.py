from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.video import SeenVideo


class VideoRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def filter_unseen(self, user_id: int, video_ids: list[str]) -> list[str]:
        if not video_ids:
            return []
        async with self._factory.begin() as session:
            stmt = select(SeenVideo.video_id).where(
                SeenVideo.user_id == user_id,
                SeenVideo.video_id.in_(video_ids),
            )
            result = await session.execute(stmt)
            seen = set(result.scalars())
            return [vid for vid in video_ids if vid not in seen]

    async def mark_many_seen(self, user_id: int, video_ids: list[str]) -> None:
        if not video_ids:
            return
        async with self._factory.begin() as session:
            stmt = (
                insert(SeenVideo)
                .values([{"user_id": user_id, "video_id": vid} for vid in video_ids])
                .on_conflict_do_nothing(index_elements=["user_id", "video_id"])
            )
            await session.execute(stmt)
