from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.channel import ChannelSubscription


class ChannelRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def subscribe(self, user_id: int, handle: str) -> None:
        async with self._factory.begin() as session:
            stmt = (
                insert(ChannelSubscription)
                .values(user_id=user_id, handle=handle)
                .on_conflict_do_nothing(index_elements=["user_id", "handle"])
            )
            await session.execute(stmt)

    async def unsubscribe(self, user_id: int, handle: str) -> None:
        async with self._factory.begin() as session:
            stmt = delete(ChannelSubscription).where(
                ChannelSubscription.user_id == user_id,
                ChannelSubscription.handle == handle,
            )
            await session.execute(stmt)

    async def get_subscriptions(self, user_id: int) -> list[str]:
        async with self._factory.begin() as session:
            stmt = (
                select(ChannelSubscription.handle)
                .where(ChannelSubscription.user_id == user_id)
                .order_by(ChannelSubscription.handle)
            )
            result = await session.execute(stmt)
            return list(result.scalars())

    async def is_subscribed(self, user_id: int, handle: str) -> bool:
        async with self._factory.begin() as session:
            stmt = select(ChannelSubscription.id).where(
                ChannelSubscription.user_id == user_id,
                ChannelSubscription.handle == handle,
            )
            result = await session.execute(stmt)
            return result.scalar() is not None
