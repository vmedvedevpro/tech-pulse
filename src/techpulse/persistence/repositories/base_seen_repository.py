from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import InstrumentedAttribute


class BaseSeenRepository:
    def __init__(
            self,
            session_factory: async_sessionmaker[AsyncSession],
            model: type[Any],
            id_attr: InstrumentedAttribute[str],
    ) -> None:
        self._factory = session_factory
        self._model: Any = model
        self._id_attr: Any = id_attr

    async def filter_unseen(self, user_id: int, ids: list[str]) -> list[str]:
        if not ids:
            return []
        async with self._factory.begin() as session:
            stmt = select(self._id_attr).where(
                self._model.user_id == user_id,
                self._id_attr.in_(ids),
            )
            result = await session.execute(stmt)
            seen = set(result.scalars())
            return [i for i in ids if i not in seen]

    async def mark_many_seen(self, user_id: int, ids: list[str]) -> None:
        if not ids:
            return
        async with self._factory.begin() as session:
            col_name = self._id_attr.key
            stmt = (
                insert(self._model)
                .values([{"user_id": user_id, col_name: i} for i in ids])
                .on_conflict_do_nothing(index_elements=["user_id", col_name])
            )
            await session.execute(stmt)
