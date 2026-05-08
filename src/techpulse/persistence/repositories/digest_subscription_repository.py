from datetime import datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.digest_subscription import DigestSubscription


class DigestSubscriptionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def subscribe(self, user_id: int) -> None:
        async with self._factory.begin() as session:
            stmt = (
                insert(DigestSubscription)
                .values(user_id=user_id)
                .on_conflict_do_nothing(index_elements=["user_id"])
            )
            await session.execute(stmt)

    async def unsubscribe(self, user_id: int) -> None:
        async with self._factory.begin() as session:
            stmt = delete(DigestSubscription).where(DigestSubscription.user_id == user_id)
            await session.execute(stmt)

    async def is_subscribed(self, user_id: int) -> bool:
        async with self._factory.begin() as session:
            stmt = select(DigestSubscription.user_id).where(DigestSubscription.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar() is not None

    async def list_due(self, threshold: datetime) -> list[int]:
        async with self._factory.begin() as session:
            stmt = select(DigestSubscription.user_id).where(
                or_(
                    DigestSubscription.last_sent_at.is_(None),
                    DigestSubscription.last_sent_at < threshold,
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars())

    async def mark_sent(self, user_id: int, sent_at: datetime) -> None:
        async with self._factory.begin() as session:
            stmt = (
                update(DigestSubscription)
                .where(DigestSubscription.user_id == user_id)
                .values(last_sent_at=sent_at)
            )
            await session.execute(stmt)
