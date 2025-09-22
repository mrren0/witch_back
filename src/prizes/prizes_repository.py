from typing import List, Optional, Sequence

from sqlalchemy import select, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.prizes.models import UnclaimedRewardModel


class PrizesCore:
    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------------------------------
    # Занести призы из result_data → unclaimed_rewards
    # -------------------------------------------------
    async def add_unclaimed_prizes_from_archive(
        self,
        event_id: int,
        result_data: Sequence[dict],
    ) -> None:
        """
        1. Удаляет старые записи данного event_id
        2. Добавляет новые (только если rewards не пустой dict/список)
        """
        # 1) чистим предыдущий импорт
        await self.session.execute(
            delete(UnclaimedRewardModel).where(UnclaimedRewardModel.event_id == event_id)
        )

        # 2) формируем список строк для массовой вставки
        rows = [
            {
                "user_id": row["user_id"],
                "event_id": event_id,
                "place": row["place"],
                "rewards": row["rewards"],
            }
            for row in result_data
            if row.get("rewards")  # пропускаем, если призов нет
        ]
        if rows:
            stmt = insert(UnclaimedRewardModel).values(rows)
            await self.session.execute(stmt)

        await self.session.commit()

    # -------------------------------------------------
    # Получить все непретензованные призы для пользователя
    # -------------------------------------------------
    async def get_unclaimed_rewards(
        self,
        user_id: int,
        event_id: Optional[int] = None,
    ) -> List[UnclaimedRewardModel]:
        conditions = [UnclaimedRewardModel.user_id == user_id]
        if event_id is not None:
            conditions.append(UnclaimedRewardModel.event_id == event_id)

        stmt = select(UnclaimedRewardModel).where(*conditions)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # -------------------------------------------------
    # Получить непретензованные призы по ивенту
    # -------------------------------------------------
    async def get_unclaimed_rewards_by_event(
        self,
        user_id: int,
        event_id: int,
    ) -> List[UnclaimedRewardModel]:
        stmt = (
            select(UnclaimedRewardModel)
            .where(
                UnclaimedRewardModel.user_id == user_id,
                UnclaimedRewardModel.event_id == event_id,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # -------------------------------------------------
    # Забрать один приз
    # -------------------------------------------------
    async def claim_reward(
        self,
        user_id: int,
        prize_id: int,
    ) -> Optional[UnclaimedRewardModel]:
        stmt = (
            select(UnclaimedRewardModel)
            .where(
                UnclaimedRewardModel.user_id == user_id,
                UnclaimedRewardModel.id == prize_id,
            )
        )
        reward = await self.session.scalar(stmt)
        if not reward:
            return None

        await self.session.delete(reward)
        await self.session.commit()
        return reward
