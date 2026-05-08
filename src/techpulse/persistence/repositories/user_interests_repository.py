from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.interest import UserInterest


class InterestsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def add_interest(self, user_id: int, interest: str) -> None:
        async with self._factory.begin() as session:
            stmt = (
                insert(UserInterest)
                .values(user_id=user_id, interest=interest)
                .on_conflict_do_nothing(index_elements=["user_id", "interest"])
            )
            await session.execute(stmt)

    async def remove_interest(self, user_id: int, interest: str) -> None:
        async with self._factory.begin() as session:
            stmt = delete(UserInterest).where(
                UserInterest.user_id == user_id,
                UserInterest.interest == interest,
            )
            await session.execute(stmt)

    async def get_interests(self, user_id: int) -> list[str]:
        async with self._factory.begin() as session:
            stmt = (
                select(UserInterest.interest)
                .where(UserInterest.user_id == user_id)
                .order_by(UserInterest.interest)
            )
            result = await session.execute(stmt)
            return list(result.scalars())

    async def has_interest(self, user_id: int, interest: str) -> bool:
        async with self._factory.begin() as session:
            stmt = select(UserInterest.id).where(
                UserInterest.user_id == user_id,
                UserInterest.interest == interest,
            )
            result = await session.execute(stmt)
            return result.scalar() is not None
