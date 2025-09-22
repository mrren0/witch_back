from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base

if TYPE_CHECKING:  # чтобы не ловить циклические импорты во время миграций
    from src.schemas.users import UserSchemaWithoutOrm


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(unique=True, index=True)
    gold: Mapped[int] = mapped_column(default=5)
    skin: Mapped[str] = mapped_column(
        default="38ef8571-0e7d-4926-88db-fcb5a8892adb"
    )
    wood: Mapped[int] = mapped_column(default=0)
    stone: Mapped[int] = mapped_column(default=0)
    grass: Mapped[int] = mapped_column(default=0)
    berry: Mapped[int] = mapped_column(default=0)
    brick: Mapped[int] = mapped_column(default=0)
    fish: Mapped[int] = mapped_column(default=0)
    boards: Mapped[int] = mapped_column(default=0)
    rope: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    token: Mapped["TokenModel"] = relationship(
        "TokenModel", uselist=False, back_populates="user"
    )

    def to_read_model_without_orm(self):  # -> UserSchemaWithoutOrm
        from src.schemas.users import UserSchemaWithoutOrm  # локальный импорт

        return UserSchemaWithoutOrm(
            id=self.id,
            phone=self.phone,
            gold=self.gold,
            skin=self.skin,
            wood=self.wood,
            stone=self.stone,
            grass=self.grass,
            berry=self.berry,
            brick=self.brick,
            fish=self.fish,
            boards=self.boards,
            rope=self.rope,
        )


class TokenModel(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["UserModel"] = relationship(
        "UserModel", uselist=False, back_populates="token"
    )


class ProductItemModel(Base):
    __tablename__ = "products_item"  # ← snake_case, без дефиса

    id: Mapped[int] = mapped_column(primary_key=True)
    skin: Mapped[str] = mapped_column(default="", server_default="")
    gold: Mapped[int] = mapped_column(default=0)
    wood: Mapped[int] = mapped_column(default=0)
    stone: Mapped[int] = mapped_column(default=0)
    grass: Mapped[int] = mapped_column(default=0)
    berry: Mapped[int] = mapped_column(default=0)
    brick: Mapped[int] = mapped_column(default=0)
    fish: Mapped[int] = mapped_column(default=0)
    boards: Mapped[int] = mapped_column(default=0)
    rope: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel", back_populates="item"
    )


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    price: Mapped[int] = mapped_column(default=0)
    id_product_item: Mapped[int] = mapped_column(ForeignKey("products_item.id"))

    item: Mapped["ProductItemModel"] = relationship(
        "ProductItemModel", back_populates="products"
    )


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(default="unknown")
    productId: Mapped[int] = mapped_column(ForeignKey("products.id"))
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    purchaseId: Mapped[str] = mapped_column(default="", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UnaddedProduct(Base):
    __tablename__ = "unadded_product"  # ← snake_case, без дефиса

    id: Mapped[int] = mapped_column(primary_key=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id"))
    productId: Mapped[int] = mapped_column(ForeignKey("products.id"))
