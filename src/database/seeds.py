from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import get_async_session
from src.database.models import TokenModel, UserModel
from src.infra.create_time import Time
from src.infra.logger import logger

MASTER_PHONE = "79094385575"
MASTER_TOKEN = "393e0c78db209ceb2cd24690fa5d8542a6da6f96"


async def ensure_master_access_token() -> None:
    """Create a default user with a master access token for manual testing."""

    async with get_async_session() as session:
        try:
            user_result = await session.execute(
                select(UserModel).where(UserModel.phone == MASTER_PHONE)
            )
            user = user_result.scalar_one_or_none()

            if user is None:
                user = UserModel(phone=MASTER_PHONE)
                session.add(user)
                await session.flush()  # Assigns the generated primary key
                logger.info("Created master test user with phone %s", MASTER_PHONE)

            token_result = await session.execute(
                select(TokenModel).where(TokenModel.id_user == user.id)
            )
            token = token_result.scalar_one_or_none()
            expires_at = Time.now_plus_hour_for_refresh_token()

            if token is None:
                token = TokenModel(
                    id_user=user.id,
                    token=MASTER_TOKEN,
                    expires_at=expires_at,
                )
                session.add(token)
                logger.info("Seeded master access token for user_id=%s", user.id)
            else:
                token.id_user = user.id
                token.token = MASTER_TOKEN
                token.expires_at = expires_at

            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("Failed to seed master access token: %s", exc)
            raise
