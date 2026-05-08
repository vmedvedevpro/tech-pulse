from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.release import SeenRelease
from techpulse.persistence.repositories.base_seen_repository import BaseSeenRepository


class ReleaseRepository(BaseSeenRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory, SeenRelease, SeenRelease.release_id)
