from typing import Optional

from src.database.models import UserModel
from src.infra.logger import logger
from src.repository.users import UserRepository
from src.schemas.tokens import TokenSchema
from src.schemas.users import UserSchema, UserSchemaForChange
from src.infra.create_time import Time


class UserCore:

    @staticmethod
    async def add_user(phone: str):
        user_create = UserCore().create_user_model(phone)
        await UserRepository().add(user_create)

    @staticmethod
    def create_user_model(phone: str) -> UserModel:
        user = UserModel(phone=phone)
        return user

    @staticmethod
    async def get_user(phone: str) -> Optional[UserSchema]:
        user = await UserRepository.get(phone)
        if user:
            token_schema = TokenSchema.from_orm(user.token) if user.token else None
            user_schema = UserSchema.from_orm(user)
            user_schema.token = token_schema
            return user_schema
        return None

    @staticmethod
    async def change_user(user: UserSchemaForChange, phone: str):
        user_from_db = await UserRepository().get(phone=phone)

        if user_from_db is None:
            logger.warning(f"User with phone {phone} not found for update")
            return

        logger.info(f'before add coins = {user.coins}')
        logger.info(f'coins to add = {user.coins}')
        user_from_db.coins = user.coins
        user_from_db.skin = user.skin

        user_from_db.common_seed = user.common_seed
        user_from_db.epic_seed = user.epic_seed
        user_from_db.rare_seed = user.rare_seed
        user_from_db.water = user.water
        user_from_db.level = user.level
        user_from_db.booster = user.booster
        user_from_db.item = user.item
        user_from_db.pot = user.pot
        user_from_db.last_active_time = Time.now()
        await UserRepository().add(user_from_db)
