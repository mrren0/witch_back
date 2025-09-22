from typing import Optional

from pydantic import BaseModel

from src.schemas.tokens import TokenSchema


class UserSchema(BaseModel):
    id: int
    phone: str
    gold: int
    skin: str
    wood: int
    stone: int
    grass: int
    token: Optional[TokenSchema]

    class Config:
        from_attributes = True


class UserSchemaForChange(BaseModel):
    gold: int
    skin: str
    wood: int
    stone: int
    grass: int
    berry: int
    brick: int
    fish: int
    boards: int
    rope: int

    model_config = {
        "from_attributes": True
    }


class UserSchemaWithoutOrm(BaseModel):
    id: int
    phone: str
    gold: int
    skin: str
    wood: int
    stone: int
    grass: int
    berry: int
    brick: int
    fish: int
    boards: int
    rope: int
