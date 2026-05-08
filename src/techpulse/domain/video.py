from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from techpulse.domain.base import Base


class SeenVideo(Base):
    __tablename__ = "seen_videos"
    __table_args__ = (UniqueConstraint("user_id", "video_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String, nullable=False)
