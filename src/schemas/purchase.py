from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field, constr


class ErrorInfo(BaseModel):
    code: str = Field(..., description="Код ошибки")
    info: Union[List[str], str, None] = Field(
        None, description="Описание ошибки, массив или строка"
    )


class PurchaseStatus(BaseModel):
    id: str
    status: constr(pattern=r"^(success|error|in_progress)$")
    productId: int
    phone: constr(pattern=r"^\+?\d{10,15}$")
    price: float
    externalId: Optional[str] = None
    error: Optional[ErrorInfo] = None


class PurchaseProductSchema(BaseModel):
    id: int
    name: str
    price: Optional[int] = None

    model_config = {
        "from_attributes": True,
    }


class PurchaseHistoryItemSchema(BaseModel):
    id: int
    product: PurchaseProductSchema
    status: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PurchaseHistoryListSchema(BaseModel):
    purchases: List[PurchaseHistoryItemSchema]

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
