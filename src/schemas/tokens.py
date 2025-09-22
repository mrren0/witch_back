from datetime import datetime

from pydantic import BaseModel


class TokenSchema(BaseModel):
    id: int
    id_user: int
    token: str
    expires_at: datetime

    class Config:
        from_attributes = True
