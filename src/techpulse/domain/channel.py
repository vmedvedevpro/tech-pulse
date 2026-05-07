from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from techpulse.domain.base import Base


class ChannelSubscription(Base):
    __tablename__ = "channel_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "handle"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    handle: Mapped[str] = mapped_column(String, nullable=False)
