from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import get_async_session
from src.database.models import ProductItemModel
from src.infra.logger import logger


class ProductItemRepository:

    @staticmethod
    async def get(id_product_item: int):
        async with get_async_session() as session:
            try:
                result = await session.execute(select(ProductItemModel).where(ProductItemModel.id == id_product_item))
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()
