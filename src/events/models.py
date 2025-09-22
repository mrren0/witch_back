from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column
from src.database.connection import Base

# Стратегия сравнения результатов для разных типов ивентов
COMPARE_STRATEGY = {
    "time": "lower",
    "score": "higher",
}


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column()
    logo: Mapped[str] = mapped_column()
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    level_ids: Mapped[list[int]] = mapped_column(JSON)

    # связь «событие → призы»
    prizes = relationship(
        "PrizeModel",               # класс объявлен ниже
        back_populates="event",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class PrizeModel(Base):
    __tablename__ = "event_prizes"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), default=-1)
    place: Mapped[int] = mapped_column()
    rewards: Mapped[dict] = mapped_column(JSON)

    # обратная связь «приз → событие»
    event = relationship(
        "EventModel",
        back_populates="prizes",
        lazy="selectin",
    )


class EventRatingModel(Base):
    __tablename__ = "event_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    result: Mapped[float] = mapped_column()


class EventHistoryModel(Base):
    __tablename__ = "event_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    results: Mapped[list[dict]] = mapped_column(JSON)
