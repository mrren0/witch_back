from typing import Optional, List

from pydantic import BaseModel


class ProductSchema(BaseModel):
    id: int
    name: str
    price: Optional[int] = 0

    model_config = {
        "from_attributes": True
    }


class ProductsListSchema(BaseModel):
    products: List[ProductSchema]

    model_config = {
        "from_attributes": True
    }
