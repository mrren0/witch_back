from fastapi import HTTPException, status

from config import SALT_BUBBLES
from src.database.models import TokenModel
from src.infra.encryption import Encryption
from src.infra.logger import logger
from src.infra.create_time import Time
from src.repository.tokens import TokenRepository


class TokenCore:
    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @staticmethod
    async def refresh_token(old_token: str) -> str:
        """
        Обновляет refresh-токен и возвращает новую строку токена.
        """
        logger.debug(f"TokenCore.refresh_token: old_token={old_token}")
        token_record = await TokenRepository().get(old_token)
        if token_record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found",
            )

        # Кэшируем идентификатор пользователя до закрытия сессии —
        # иначе при логировании поймаем DetachedInstanceError
        user_id = token_record.id_user

        # Генерируем новый токен
        new_token = Encryption().hash_str(
            token_record.user.phone,
            SALT_BUBBLES,
            str(Time().now()),
        )
        token_record.token = new_token
        token_record.expires_at = Time.now_plus_hour_for_refresh_token()

        await TokenRepository().add(token_record)
        logger.info(f"Refresh token updated for user_id={user_id}")
        return new_token

    @staticmethod
    async def is_access_token(access_token: str) -> TokenModel:
        """
        Проверяет валидность access_token:
        * возвращает TokenModel, если всё ок
        * бросает HTTPException 401, если токен не найден или истёк
        """
        token_record = await TokenRepository().get(access_token)
        if token_record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            )

        # мастер-токен для локалки
        if access_token == "393e0c78db209ceb2cd24690fa5d8542a6da6f96":
            logger.debug("Master token used")
            return token_record

        if Time().now() > token_record.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token expired",
            )

        return token_record

    @staticmethod
    async def get_user_by_token(access_token: str):
        """Возвращает пользователя по валидному access_token либо 401."""
        token_record = await TokenCore.is_access_token(access_token)
        return token_record.user

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    async def add_token(user_id: int, token: str) -> None:
        token_model = TokenCore.create_token_model(user_id, token)
        logger.info(f"New token created: user_id={token_model.id_user}")
        await TokenRepository().add(token_model)

    @staticmethod
    def create_token_model(user_id: int, token: str) -> TokenModel:
        return TokenModel(
            id_user=user_id,
            token=token,
            expires_at=Time.now_plus_hour_for_refresh_token(),
        )

    @staticmethod
    async def create_and_store_token(user_id: int, login: str) -> str:
        token = Encryption().hash_str(login, SALT_BUBBLES, str(Time().now()))
        await TokenCore.add_token(user_id, token)
        return token
