from pydantic import BaseModel, ConfigDict


class RouletteItemSchema(BaseModel):
    item: str
    quantity: int
    chance: float

    model_config = ConfigDict(from_attributes=True)
