from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RouletteItemModel


class RouletteRepository:
    """Работа с таблицей элементов рулетки."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_items(self, user_id: int, limit: int = 8) -> list[RouletteItemModel]:
        result = await self._session.execute(
            select(RouletteItemModel)
            .where(RouletteItemModel.user_id == user_id)
            .order_by(RouletteItemModel.id)
            .limit(limit)
        )
        return list(result.scalars().all())
