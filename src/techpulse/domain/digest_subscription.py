from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from techpulse.domain.base import Base


class DigestSubscription(Base):
    __tablename__ = "digest_subscriptions"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
