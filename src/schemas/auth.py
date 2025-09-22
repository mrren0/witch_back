from pydantic import BaseModel


class AuthUser(BaseModel):
    login: str


class AuthResponse(BaseModel):
    accessToken: str
    expires_at: str
