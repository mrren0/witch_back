from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import get_async_session
from src.database.models import ProductModel
from src.infra.logger import logger


class ProductRepository:

    @staticmethod
    async def get_all():
        async with get_async_session() as session:
            try:
                result = await session.execute(select(ProductModel))
                return result.scalars().all()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()

    @staticmethod
    async def get(productId: int):
        async with get_async_session() as session:
            try:
                result = await session.execute(select(ProductModel).where(ProductModel.id == productId))
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()
