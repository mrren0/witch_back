from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import get_async_session
from src.database.models import TransactionModel
from src.infra.logger import logger


class TransactionRepository:

    @staticmethod
    async def add(transaction: TransactionModel):
        async with get_async_session() as session:
            try:
                session.add(transaction)
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()

    @staticmethod
    async def get(purchaseId: str):
        async with get_async_session() as session:
            try:
                query = select(TransactionModel).where(TransactionModel.purchaseId == purchaseId)
                result = await session.execute(query)
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()
