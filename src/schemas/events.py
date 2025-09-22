# src/schemas/events.py
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


class PrizeDTO(BaseModel):
    place: int
    # поддерживаем числовые и строковые значения
    rewards: Dict[str, Union[str, int]]


class EventPublicDTO(BaseModel):
    id: int
    name: str
    event_type: str
    logo: str
    start: Optional[datetime] = Field(None, alias="start_at")
    finish: Optional[datetime] = Field(None, alias="finish_at")
    description: Optional[str]
    level_ids: List[str]
    prizes: List[PrizeDTO]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="ignore",
    )


class LeaderboardEntry(BaseModel):
    user_id: int
    result: int
    user_name: str = Field(
        ..., example="+7012***6704",
        description="Телефонный номер, в котором средние цифры замаскированы"
    )
    place: int
    rewards: Dict[str, Union[str, int]]

    class Config:
        extra = 'ignore'


class CurrentUserStats(BaseModel):
    user_id: int
    result: int
    rewards: Dict[str, Union[str, int]]
    place: int


class LeaderboardResponse(BaseModel):
    top: List[LeaderboardEntry]
    current_user: CurrentUserStats

    class Config:
        extra = 'ignore'
