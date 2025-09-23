from fastapi import APIRouter, Header, HTTPException

from src.business_logic.roulette import RouletteCore
from src.business_logic.token import TokenCore
from src.database.connection import get_async_session
from src.schemas.roulette import RouletteItemSchema


router = APIRouter(prefix="/api/roulette", tags=["Roulette"])


@router.get("", response_model=list[RouletteItemSchema])
async def get_roulette_items(accessToken: str | None = Header(default=None)) -> list[RouletteItemSchema]:
    if not accessToken:
        raise HTTPException(status_code=401, detail="NO_TOKEN")

    user = await TokenCore.get_user_by_token(accessToken)

    async with get_async_session() as session:
        return await RouletteCore(session).get_user_items(user.id)
