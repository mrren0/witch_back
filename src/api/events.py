from fastapi import APIRouter, Header, HTTPException, Query, Body
from src.events.repository import EventRatingCore
from src.database.connection import get_async_session
from src.business_logic.token import TokenCore
from src.events.DTO import (
    EventPublicDTO,
    LeaderboardResponse,
)

router = APIRouter(prefix="/api/event", tags=["Events"])


@router.get("/current", response_model=list[EventPublicDTO], response_model_exclude_none=True)
async def get_current_events() -> list[EventPublicDTO]:
    async with get_async_session() as session:
        core = EventRatingCore(session)
        return await core.get_current_events_with_prizes()


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    event_id: int = Query(..., ge=1, description="ID события"),
    limit: int = Query(10, ge=1, le=100, description="Сколько пользователей вернуть в топ-списке"),
    accessToken: str | None = Header(None),
):
    if not accessToken:
        raise HTTPException(status_code=401, detail="NO_TOKEN")

    async with get_async_session() as session:
        # Используем токен как в проекте
        user = await TokenCore.get_user_by_token(accessToken)
        if not user:
            raise HTTPException(status_code=401, detail="INVALID_TOKEN")

        top, cur = await EventRatingCore(session).get_leaderboard(
            event_id=event_id,
            current_user_id=user.id,
            top_n=limit,
        )
        return {
            "top": [
                {
                    "user_id": r["user_id"],
                    "result": r["result"],
                    "user_name": r["user_name"],
                    "place": r["place"],
                    "rewards": r["rewards"],
                }
                for r in top
            ],
            "current_user": cur,
        }


@router.post("/result")
async def submit_event_result(
    event_id: int = Query(..., ge=1),
    accessToken: str | None = Header(None),
    body: float = Body(..., description="Добавочный результат"),
):
    if not accessToken:
        raise HTTPException(status_code=401, detail="NO_TOKEN")

    async with get_async_session() as session:
        user = await TokenCore.get_user_by_token(accessToken)
        if not user:
            raise HTTPException(status_code=401, detail="INVALID_TOKEN")

        new_total, place = await EventRatingCore(session).submit_event_result(
            user_id=user.id,
            event_id=event_id,
            result=body,
        )
        # Вернули старый формат:
        return {"result": new_total, "place": place}
