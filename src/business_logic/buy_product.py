import asyncio
from datetime import timedelta

import httpx
from fastapi import HTTPException
from starlette.responses import JSONResponse

from config import SECRET_FOR_BEELINE
from src.business_logic.transaction import TransactionCore
from src.infra.encryption import Encryption
from src.infra.logger import logger
from src.infra.radis import Redis
from src.infra.create_time import Time


class BuyProductBeeline:
    url = 'https://api.partnerka.beeline.ru'  # взял из рози

    @classmethod
    async def buy_product(cls, phone, productId):
        count = 0
        token = await BuyProductBeeline.get_token(phone)
        buy_url = cls.url + f'/v2/game/purchase-async?appID=arkom&token={token}'
        headers = {"accept": "application/json"}
        time = Time().now().isoformat()
        signature = Encryption().hash_str(phone + str(productId) + str(time) + SECRET_FOR_BEELINE)
        data = {
            'phone': phone,
            'productId': productId,
            'time': time,
            'signature': signature,
            'callback': 'https://survislebeeline.arcomm.ru/api/game/pay-product'
        }
        logger.info(f'data = {data}')

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.post(buy_url, json=data, headers=headers)
                logger.info(f'Запрос на покупку отправлен количество раз {count}')
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error occurred while requesting {exc.request.url!r}.")
        count += 1
        if response.status_code == 200:
            logger.info(f'Запрос билайну покупку прошел успешно')
            response_data = response.json()
            purchaseId = response_data.get("purchaseId")
            await TransactionCore().add_transaction(phone, purchaseId, productId)
        else:
            logger.error(f'Запрос билайну покупку прошел не успешно')
            logger.error(f'ошибка = {response.text}')

        await asyncio.sleep(3)

        attempts = 0
        while attempts < 5:
            logger.info(f'{attempts} попытка взять данные из Redis')
            status = Redis.get_status_purchase(phone)
            if status == 'success':
                logger.info(f'возвращаю 200')
                return JSONResponse(status_code=200, content='transaction processed success')
            if status == 'error':
                logger.info(f'возвращаю 402')
                raise HTTPException(status_code=402, detail="not enough funds to buy")
            if status == 'in_progress':
                logger.info(f'возвращаю 403')
                raise HTTPException(status_code=403, detail="in_progress")
            attempts += 1
            await asyncio.sleep(3)
        logger.info(f'возвращаю 403')
        raise HTTPException(status_code=403, detail="not enough funds to buy")

    @classmethod
    async def get_token(cls, phone):
        get_token_url = cls.url + f'/v2/game/token'
        headers = {"accept": "application/json"}
        time = Time().now().isoformat()
        signature = Encryption().hash_str('arkom' + phone + str(time) + SECRET_FOR_BEELINE)
        data = {
            'appID': 'arkom',
            'phone': phone,
            'time': time,
            'signature': signature
        }
        logger.info(f"time = {time}, signature_data = arkom {phone}{time}{SECRET_FOR_BEELINE}, signature = {signature}")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.post(get_token_url, json=data, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error occurred while requesting {exc.request.url!r}.")

        if response.status_code == 200:
            response_data = response.json()
            token = response_data.get("token")
            logger.info(f'Запрос билайну на получение токена прошел успешно')
        else:
            logger.info(f'ошибка = {response.text}')
            token = None
            logger.info(f'Запрос билайну на получение токена прошел не успешно')
        logger.info(f'token = {token}')
        return token
