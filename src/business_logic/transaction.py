from fastapi import HTTPException

from src.database.models import TransactionModel
from src.repository.transaction import TransactionRepository
from src.repository.users import UserRepository
from src.schemas.purchase import (
    PurchaseHistoryItemSchema,
    PurchaseHistoryListSchema,
    PurchaseProductSchema,
)


class TransactionCore:

    @staticmethod
    async def add_transaction(
            phone: str,
            purchaseId: str,
            productId: int
    ):
        user = await UserRepository().get(phone)
        transaction_model = TransactionCore().create_transaction_model(
            productId, user.id, purchaseId
        )

        await TransactionRepository().add(transaction_model)

    @staticmethod
    async def change_status(
            transaction: TransactionModel,
            status: str
    ):
        transaction.status = status
        await TransactionRepository().add(transaction)

    @staticmethod
    async def get_transaction(
            purchaseId: str,
    ):
        transaction = await TransactionRepository().get(purchaseId)
        if transaction is None:
            raise HTTPException(status_code=404, detail="transaction not found")
        return transaction

    @staticmethod
    def create_transaction_model(
            productId: int,
            id_user: int,
            purchaseId: str
    ) -> TransactionModel:
        transaction_model = TransactionModel(
            productId=productId,
            id_user=id_user,
            purchaseId=purchaseId
        )
        return transaction_model

    @staticmethod
    async def get_user_purchases(user_id: int) -> PurchaseHistoryListSchema:
        transactions = await TransactionRepository().list_by_user(user_id)
        purchase_items: list[PurchaseHistoryItemSchema] = []

        for transaction, product in transactions:
            product_schema = (
                PurchaseProductSchema.model_validate(product)
                if product is not None
                else PurchaseProductSchema(
                    id=transaction.productId,
                    name="Unknown product",
                    price=None,
                )
            )

            purchase_items.append(
                PurchaseHistoryItemSchema(
                    id=transaction.id,
                    status=transaction.status,
                    product=product_schema,
                    created_at=transaction.created_at,
                )
            )

        return PurchaseHistoryListSchema(purchases=purchase_items)
