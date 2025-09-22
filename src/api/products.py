from fastapi import APIRouter

from src.business_logic.product import ProductCore


router = APIRouter(
    prefix="/api/product",
    tags=["Product"],
)


@router.get('')
async def get_all_product_api():
    products = await ProductCore().get_all()
    return products.model_dump()
