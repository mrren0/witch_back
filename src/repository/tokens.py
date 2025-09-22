from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from src.database.connection import get_async_session
from src.database.models import TokenModel
from src.infra.logger import logger


class TokenRepository:

    @staticmethod
    async def add(token: TokenModel):
        async with get_async_session() as session:
            try:
                session.add(token)
                await session.commit()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()

    @staticmethod
    async def get(accessToken: str) -> TokenModel:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(TokenModel)
                    .options(joinedload(TokenModel.user))
                    .where(TokenModel.token == accessToken)
                )
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()
