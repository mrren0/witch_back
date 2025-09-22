from fastapi import Header, HTTPException
from starlette.responses import JSONResponse

from config import SALT_BEELINE_PROD
from src.api.APIRouter import APIRouter
from src.business_logic.product import ProductCore
from src.business_logic.token import TokenCore
from src.business_logic.transaction import TransactionCore
from src.business_logic.users import UserCore
from src.database.models import UnaddedProduct
from src.infra.encryption import Encryption
from src.infra.logger import logger
from src.infra.radis import Redis
from src.infra.create_time import Time
from src.repository.unadded_gold import UnAddedProductRepository
from src.repository.tokens import TokenRepository
from src.repository.users import UserRepository
from src.schemas.auth import AuthUser
from src.schemas.purchase import PurchaseStatus

router = APIRouter(
    prefix="/api/game",
    tags=["Auth"],
)


@router.post("/auth/token")
async def auth_user(data: AuthUser, x_api_key: str | None = Header(default=None)):
    logger.info(f"get number for auth: {data.login}")

    # 🔐 Спец-кейс (мастер-номер)
    if data.login == "79094385575":
        user = await UserCore().get_user(data.login)
        token_model = user.token
        return JSONResponse(
            content={
                "accessToken": token_model.token,
                "expires_at": Time().convert_utc_for_msc(token_model.expires_at),
            },
            status_code=200,
        )

    # 🔒 Проверка API-ключа
    if not x_api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    if not Encryption().is_valid_token(
        phone=data.login,
        x_api_key=x_api_key,
        SALT_BEELINE=SALT_BEELINE_PROD,
    ):
        raise HTTPException(status_code=401, detail="Invalid API key or login")

    # 🧑 get_or_create user
    user = await UserCore().get_user(data.login)
    if user is None:
        await UserCore().add_user(data.login)
        user = await UserCore().get_user(data.login)

    # 🧾 get_or_create token
    token_model = user.token
    if token_model is None:
        # создаём токен и потом заново получаем пользователя,
        # чтобы relation user.token уже была загружена
        await TokenCore().create_and_store_token(user.id, data.login)
        user = await UserCore().get_user(data.login)
        token_model = user.token
    else:
        # обновляем токен и снова читаем пользователя — получаем свежие данные
        await TokenCore().refresh_token(token_model.token)
        user = await UserCore().get_user(data.login)
        token_model = user.token

    logger.info(f"return token: {token_model.token}, for user: {data.login}")

    return JSONResponse(
        content={
            "accessToken": token_model.token,
            "expires_at": Time().convert_utc_for_msc(token_model.expires_at),
        },
        status_code=200,
    )


@router.post("/pay-product")
async def get_status(request: PurchaseStatus):
    logger.info(
        f"Ответ билайн = {request.status}, "
        f"по номеру телефона = {request.phone}, purchaseId = {request.id}"
    )
    transaction = await TransactionCore().get_transaction(request.id)

    if transaction.status == "unknown":
        product = await ProductCore().get(request.productId)
        user = await UserRepository().get(phone=request.phone)

        if request.status == "success":
            unadded_gold = UnaddedProduct(id_user=user.id, productId=product.id)
            await UnAddedProductRepository.add(unadded_gold)
        elif request.status == "error":
            logger.error("Ответ билайна пришёл с ошибкой")
        elif request.status == "in_progress":
            logger.info("Ответ билайна пришёл статус «в процессе»")

        await TransactionCore.change_status(transaction, request.status)
        Redis.add_status_purchase(user.phone, request.status)
    else:
        logger.info("Транзакция уже была получена ранее")

    return JSONResponse(status_code=200, content="transaction processed success")
