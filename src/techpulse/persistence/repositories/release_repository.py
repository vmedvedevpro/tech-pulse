from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.release import SeenRelease


class ReleaseRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def filter_unseen(self, user_id: int, release_ids: list[str]) -> list[str]:
        if not release_ids:
            return []
        async with self._factory.begin() as session:
            stmt = select(SeenRelease.release_id).where(
                SeenRelease.user_id == user_id,
                SeenRelease.release_id.in_(release_ids),
            )
            result = await session.execute(stmt)
            seen = set(result.scalars())
            return [rid for rid in release_ids if rid not in seen]

    async def mark_many_seen(self, user_id: int, release_ids: list[str]) -> None:
        if not release_ids:
            return
        async with self._factory.begin() as session:
            stmt = (
                insert(SeenRelease)
                .values([{"user_id": user_id, "release_id": rid} for rid in release_ids])
                .on_conflict_do_nothing(index_elements=["user_id", "release_id"])
            )
            await session.execute(stmt)
