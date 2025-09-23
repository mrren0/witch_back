from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.schemas.tokens import TokenSchema


class UserSchema(BaseModel):
    id: int
    phone: str
    skin: str
    coins: int
    common_seed: int
    epic_seed: int
    rare_seed: int
    water: int
    level: int
    booster: int
    item: int
    pot: int
    created_at: datetime
    last_update: datetime
    token: Optional[TokenSchema]

    class Config:
        from_attributes = True


class UserSchemaForChange(BaseModel):
    skin: str
    coins: int
    common_seed: int
    epic_seed: int
    rare_seed: int
    water: int
    level: int
    booster: int
    item: int
    pot: int

    model_config = {
        "from_attributes": True
    }


class UserSchemaWithoutOrm(BaseModel):
    id: int
    phone: str
    skin: str
    coins: int
    common_seed: int
    epic_seed: int
    rare_seed: int
    water: int
    level: int
    booster: int
    item: int
    pot: int
    created_at: datetime
    last_update: datetime
