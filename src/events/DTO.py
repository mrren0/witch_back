# src/events/DTO.py
from __future__ import annotations

"""Survive — Events Pydantic DTOs."""

from datetime import datetime
from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field, ConfigDict


class PrizeEntry(BaseModel):
    """Prize line with place and flat rewards dict.
    Для закрывшегося события сюда может подмешиваться телефон победителя.
    """
    place: int
    # Поддерживаем строковые и числовые значения призов
    rewards: Dict[str, Union[str, int]]
    phone: Optional[str] = None


class EventModelDTO(BaseModel):
    """Мини-версия события без призов."""
    id: int
    name: str
    event_type: str
    logo: Optional[str] = None
    start_date: datetime
    end_date: datetime
    level_ids: List[Union[int, str]] = Field(..., alias="level_id")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
    )


class EventPublicDTO(EventModelDTO):
    """То же событие + призы."""
    prizes: List[PrizeEntry] = []


class EventResultResponse(BaseModel):
    ok: bool = True


class LeaderboardEntry(BaseModel):
    user_id: int
    result: float
    user_name: str = Field(
        ...,
        example="+7012***6704",
        description="Телефонный номер, в котором средние цифры замаскированы",
    )
    place: int
    rewards: Optional[Dict[str, Union[str, int]]] = None

    @staticmethod
    def _mask(phone: str) -> str:
        """Маска: показываем первые 4 и последние 4 цифры, середину скрываем.
        Пример: +7012***6704
        """
        if not phone:
            return phone
        digits = "".join(ch for ch in phone if ch.isdigit())
        # если слишком мало цифр — не маскируем
        if len(digits) < 8:
            return phone
        first4 = digits[:4]
        last4 = digits[-4:]
        plus = "+" if phone.strip().startswith("+") else ""
        return f"{plus}{first4}***{last4}"


class CurrentUserInfo(BaseModel):
    user_id: int
    result: float
    place: int
    rewards: Optional[Dict[str, Union[str, int]]] = None


class LeaderboardResponse(BaseModel):
    top: List[LeaderboardEntry]
    current_user: Optional[CurrentUserInfo] = None


__all__ = [
    "EventModelDTO",
    "EventPublicDTO",
    "EventResultResponse",
    "LeaderboardResponse",
    "LeaderboardEntry",
    "CurrentUserInfo",
    "PrizeEntry",
]
