from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from src.database.connection import get_async_session
from src.database.models import UserModel
from src.infra.logger import logger


class UserRepository():

    @staticmethod
    async def add(user: UserModel):
        async with get_async_session() as session:
            try:
                session.add(user)
                await session.commit()  # Сначала коммитим
                await session.refresh(user)  # Обновляем объект
                return user
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()

    @staticmethod
    async def get(phone: str) -> UserModel | None:
        async with get_async_session() as session:
            try:
                result = await session.execute(
                    select(UserModel)
                    .options(joinedload(UserModel.token))
                    .where(UserModel.phone == phone)
                )
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(e)
                await session.rollback()
