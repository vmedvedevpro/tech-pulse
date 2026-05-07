from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.repo import UserRepo


class RepoRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def add_repo(self, user_id: int, repo: str) -> None:
        async with self._factory.begin() as session:
            stmt = (
                insert(UserRepo)
                .values(user_id=user_id, repo=repo)
                .on_conflict_do_nothing(index_elements=["user_id", "repo"])
            )
            await session.execute(stmt)

    async def remove_repo(self, user_id: int, repo: str) -> None:
        async with self._factory.begin() as session:
            stmt = delete(UserRepo).where(
                UserRepo.user_id == user_id,
                UserRepo.repo == repo,
            )
            await session.execute(stmt)

    async def get_repos(self, user_id: int) -> list[str]:
        async with self._factory.begin() as session:
            stmt = (
                select(UserRepo.repo)
                .where(UserRepo.user_id == user_id)
                .order_by(UserRepo.repo)
            )
            result = await session.execute(stmt)
            return list(result.scalars())

    async def has_repo(self, user_id: int, repo: str) -> bool:
        async with self._factory.begin() as session:
            stmt = select(UserRepo.id).where(
                UserRepo.user_id == user_id,
                UserRepo.repo == repo,
            )
            result = await session.execute(stmt)
            return result.scalar() is not None
