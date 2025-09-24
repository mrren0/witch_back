from fastapi import APIRouter, Header, HTTPException, Request
from starlette.responses import JSONResponse

from src.business_logic.buy_product import BuyProductBeeline
from src.business_logic.token import TokenCore
from src.business_logic.transaction import TransactionCore
from fastapi.encoders import jsonable_encoder

from src.business_logic.users import UserCore
from src.repository.product import ProductRepository
from src.repository.productItems import ProductItemRepository
from src.repository.unadded_gold import UnAddedProductRepository
from src.schemas.purchase import PurchaseHistoryListSchema
from src.schemas.users import UserSchemaForChange

router = APIRouter(prefix="/api/user", tags=["User"])


async def add_item_product(user, items_product) -> UserSchemaForChange:
    if items_product.skin:
        user.skin = items_product.skin
    if items_product.coins:
        user.coins += items_product.coins
    if items_product.common_seed:
        user.common_seed += items_product.common_seed
    if items_product.epic_seed:
        user.epic_seed += items_product.epic_seed
    if items_product.rare_seed:
        user.rare_seed += items_product.rare_seed
    if items_product.water:
        user.water += items_product.water
    if items_product.level:
        user.level += items_product.level
    if items_product.booster:
        user.booster += items_product.booster
    if items_product.item:
        user.item += items_product.item
    if items_product.pot:
        user.pot += items_product.pot

    return UserSchemaForChange(
        coins=user.coins,
        skin=user.skin,
        common_seed=user.common_seed,
        epic_seed=user.epic_seed,
        rare_seed=user.rare_seed,
        water=user.water,
        level=user.level,
        booster=user.booster,
        item=user.item,
        pot=user.pot,
    )


async def _require_token(access_token: str | None):
    if access_token is None:
        raise HTTPException(status_code=400, detail="accessToken header missing")

    return await TokenCore().is_access_token(access_token)


@router.get("")  # конечный URL: /api/user
async def get_user_api(
    request: Request,
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    token = await _require_token(accessToken)
    user = token.user

    un_added = await UnAddedProductRepository.get_one(user.id)
    if un_added:
        product = await ProductRepository().get(un_added.productId)
        items_product = await ProductItemRepository.get(product.id_product_item)

        user_changed = await add_item_product(user, items_product)
        await UserCore().change_user(user_changed, user.phone)

        token = await _require_token(accessToken)
        user = token.user
        await UnAddedProductRepository().delete_one(un_added.id)

    user_payload = user.to_read_model_without_orm().model_dump(mode="json")
    return JSONResponse(content=jsonable_encoder(user_payload), status_code=200)


async def _change_user_data(
    user_to_save: UserSchemaForChange,
    accessToken: str | None,
) -> JSONResponse:
    """Validate the access token and persist the provided user payload."""

    token = await _require_token(accessToken)
    await UserCore().change_user(user_to_save, token.user.phone)

    return JSONResponse(content={"detail": "change success"}, status_code=200)


@router.get("/purchases", response_model=PurchaseHistoryListSchema)
async def get_user_purchases(
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    token = await _require_token(accessToken)
    purchases = await TransactionCore().get_user_purchases(token.user.id)
    return purchases


@router.put("")  # конечный URL: /api/user
async def save_user(
    user_to_save: UserSchemaForChange,
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    return await _change_user_data(user_to_save, accessToken)


@router.post("")  # конечный URL: /api/user
async def save_user_post(
    user_to_save: UserSchemaForChange,
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    return await _change_user_data(user_to_save, accessToken)


@router.post("/buy")  # конечный URL: /api/user/buy
async def buy_product(
    productId: int,
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    token = await _require_token(accessToken)
    return await BuyProductBeeline().buy_product(token.user.phone, productId)
