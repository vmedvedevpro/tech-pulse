from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from techpulse.domain.video import SeenVideo
from techpulse.persistence.repositories.base_seen_repository import BaseSeenRepository


class SeenVideoRepository(BaseSeenRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory, SeenVideo, SeenVideo.video_id)
