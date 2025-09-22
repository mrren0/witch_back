from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    JSON,
    UniqueConstraint,
)

from src.database.connection import Base  # единая metadata для Alembic


class UnclaimedRewardModel(Base):
    __tablename__ = "unclaimed_rewards"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_reward_user_event"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    place = Column(Integer, nullable=False)
    rewards = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
