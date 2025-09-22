from pydantic import BaseModel, Field, constr
from typing import Optional, Union, List


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
