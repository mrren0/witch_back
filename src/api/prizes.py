from fastapi import APIRouter, Header, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_async_session
from src.business_logic.token import TokenCore
from src.prizes.prizes_repository import PrizesCore

router = APIRouter(
    prefix="/api/prizes",
    tags=["Prizes"],
)


@router.get("/unclaimed")
async def get_unclaimed_rewards(
    accessToken: str | None = Header(default=None)
):
    """
    Все незабранные призы текущего пользователя.
    """
    user = await TokenCore.get_user_by_token(accessToken)
    user_id = user.id

    async with get_async_session() as session:
        rewards = await PrizesCore(session).get_unclaimed_rewards(user_id)
        return [
            {
                "reward_id": r.id,
                "event_id": r.event_id,
                "place": r.place,
                "rewards": r.rewards,
                "created": r.created_at,
            }
            for r in rewards
        ]


@router.post("/claim")
async def claim_reward(
    prize_id: int = Body(...),
    accessToken: str | None = Header(default=None)
):
    """
    Забрать конкретный приз по `prize_id`.
    """
    user = await TokenCore.get_user_by_token(accessToken)
    user_id = user.id

    async with get_async_session() as session:
        prize = await PrizesCore(session).claim_reward(user_id, prize_id)
        if not prize:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prize not found"
            )

        # фиксируем удаление в БД
        await session.commit()

        # возвращаем данные забранного приза
        return {
            "reward_id": prize.id,
            "event_id": prize.event_id,
            "place": prize.place,
            "rewards": prize.rewards,
            "created": prize.created_at,
        }
