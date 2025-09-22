from fastapi import APIRouter, Header, HTTPException, Request
from starlette.responses import JSONResponse

from src.business_logic.buy_product import BuyProductBeeline
from src.business_logic.token import TokenCore
from src.business_logic.users import UserCore
from src.infra.logger import logger
from src.repository.product import ProductRepository
from src.repository.productItems import ProductItemRepository
from src.repository.unadded_gold import UnAddedProductRepository
from src.schemas.users import UserSchemaForChange

router = APIRouter(prefix="/api/user", tags=["User"])


async def add_item_product(user, items_product):
    if items_product.skin:
        user.skin = items_product.skin
    if items_product.gold:
        user.gold += items_product.gold
    if items_product.wood:
        user.wood += items_product.wood
    if items_product.stone:
        user.stone += items_product.stone
    if items_product.grass:
        user.grass += items_product.grass
    if items_product.berry:
        user.berry += items_product.berry
    if items_product.brick:
        user.brick += items_product.brick
    if items_product.fish:
        user.fish += items_product.fish
    if items_product.boards:
        user.boards += items_product.boards
    if items_product.rope:
        user.rope += items_product.rope

    return UserSchemaForChange(
        gold=user.gold,
        skin=user.skin,
        wood=user.wood,
        stone=user.stone,
        grass=user.grass,
        berry=user.berry,
        brick=user.brick,
        fish=user.fish,
        boards=user.boards,
        rope=user.rope,
    )


@router.get("")        # конечный URL: /api/user
async def get_user_api(
    request: Request,
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    if accessToken is None:
        raise HTTPException(status_code=400, detail="accessToken header missing")

    token = await TokenCore().is_access_token(accessToken)
    user = token.user

    un_added = await UnAddedProductRepository.get_one(user.id)
    if un_added:
        product = await ProductRepository().get(un_added.productId)
        items_product = await ProductItemRepository.get(product.id_product_item)

        user_changed = await add_item_product(user, items_product)
        await UserCore().change_user(user_changed, user.phone)

        token = await TokenCore().is_access_token(accessToken)
        user = token.user
        await UnAddedProductRepository().delete_one(un_added.id)

    return JSONResponse(content=user.to_read_model_without_orm().dict(), status_code=200)


@router.put("")        # конечный URL: /api/user
async def save_user(
    user_to_save: UserSchemaForChange,
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    if accessToken is None:
        raise HTTPException(status_code=400, detail="accessToken header missing")

    token = await TokenCore().is_access_token(accessToken)
    await UserCore().change_user(user_to_save, token.user.phone)
    return JSONResponse(content="change success", status_code=200)


@router.post("/buy")   # конечный URL: /api/user/buy
async def buy_product(
    productId: int,
    accessToken: str | None = Header(default=None, alias="accessToken"),
):
    if accessToken is None:
        raise HTTPException(status_code=400, detail="accessToken header missing")

    token = await TokenCore().is_access_token(accessToken)
    return await BuyProductBeeline().buy_product(token.user.phone, productId)
