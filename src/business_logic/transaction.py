from fastapi import HTTPException

from src.database.models import TransactionModel
from src.repository.transaction import TransactionRepository
from src.repository.users import UserRepository


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
