from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import get_async_session
from src.database.models import UnaddedProduct
from src.infra.logger import logger


class UnAddedProductRepository:

    @staticmethod
    async def get_one(id_user: int):
        async with get_async_session() as session:
            try:
                result = await session.execute(select(UnaddedProduct).where(UnaddedProduct.id_user == id_user))
                return result.scalars().first()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()

    @staticmethod
    async def add(un_added_product: UnaddedProduct):
        async with get_async_session() as session:
            try:
                session.add(un_added_product)
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()

    @staticmethod
    async def delete_one(id_un_added_gold: int):
        async with get_async_session() as session:
            try:
                await session.execute(delete(UnaddedProduct).where(UnaddedProduct.id == id_un_added_gold))
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()
