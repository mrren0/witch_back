import redis

from src.infra.logger import logger

redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)


class Redis:

    @staticmethod
    def add_status_purchase(phone: str, status: str):
        logger.info(f'добавил в редис {phone}, {status}')
        redis_client.set(phone, status, ex=600)

    @staticmethod
    def get_status_purchase(phone):
        logger.info(f'взял из редис {phone}, {redis_client.get(phone)}')
        return redis_client.get(phone)
