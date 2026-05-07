from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from techpulse.domain.base import Base


class UserRepo(Base):
    __tablename__ = "user_repos"
    __table_args__ = (UniqueConstraint("user_id", "repo"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    repo: Mapped[str] = mapped_column(String, nullable=False)
