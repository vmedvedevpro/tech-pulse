from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from techpulse.domain.base import Base


class SeenRelease(Base):
    __tablename__ = "seen_releases"
    __table_args__ = (UniqueConstraint("user_id", "release_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    release_id: Mapped[str] = mapped_column(String, nullable=False)
