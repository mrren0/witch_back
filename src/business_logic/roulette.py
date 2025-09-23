from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.roulette import RouletteRepository
from src.schemas.roulette import RouletteItemSchema


class RouletteCore:
    """Бизнес-логика работы с рулеткой."""

    def __init__(self, session: AsyncSession) -> None:
        self._repository = RouletteRepository(session)

    async def get_user_items(self, user_id: int) -> list[RouletteItemSchema]:
        items = await self._repository.get_user_items(user_id=user_id)
        return [
            RouletteItemSchema.model_validate(item, from_attributes=True)
            for item in items
        ]
