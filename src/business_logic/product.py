from fastapi import HTTPException

from src.repository.product import ProductRepository
from src.schemas.product import ProductSchema, ProductsListSchema


class ProductCore:

    @staticmethod
    async def get_all():
        products = await ProductRepository().get_all()
        pydantic_products = [ProductSchema.model_validate(product) for product in products]
        return ProductsListSchema(products=pydantic_products)

    @staticmethod
    async def get(productId: int):
        product = await ProductRepository().get(productId)
        if product is None:
            raise HTTPException(status_code=404, detail="product not found")
        return product
