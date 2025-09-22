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
        logger.info(f'before add gold = {user.gold}')
        logger.info(f'gold to add = {user.gold}')
        user_from_db.gold = user.gold
        user_from_db.skin = user.skin
        user_from_db.wood = user.wood
        user_from_db.stone = user.stone
        user_from_db.grass = user.grass
        user_from_db.berry = user.berry
        user_from_db.brick = user.brick
        user_from_db.fish = user.fish
        user_from_db.boards = user.boards
        user_from_db.rope = user.rope
        user_from_db.last_update = Time.now()
        await UserRepository().add(user_from_db)
