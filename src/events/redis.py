import json
from datetime import datetime
from typing import Any
from src.infra.create_time import Time
from src.infra.radis import redis_client
from src.infra.logger import logger
from src.events.models import EventModel


class RedisEventCache:

    @staticmethod
    def _key(event_id: int) -> str:
        return f"event_info:{event_id}"

    @classmethod
    def get(cls, event_id: int) -> EventModel | None:
        key = cls._key(event_id)
        data = redis_client.get(key)
        if not data:
            logger.info(f"[REDIS] MISS {key}")
            return None
        logger.info(f"[REDIS] HIT {key}")
        try:
            raw = json.loads(data)
            return EventModel(
                id=raw["id"],
                name=raw["name"],
                event_type=raw["event_type"],
                start_date=datetime.fromisoformat(raw["start_date"]),
                end_date=datetime.fromisoformat(raw["end_date"]),
                logo=raw["logo"],
                level_ids=raw["level_ids"],
            )
        except Exception as e:
            logger.warning(f"[REDIS] Failed to decode {key}: {e}")
            return None

    @classmethod
    def set(cls, event_id: int, event: EventModel, expires_at: datetime):
        key = cls._key(event_id)
        ttl = int((expires_at - Time.now()).total_seconds())
        if ttl <= 0:
            return
        data = {
            "id": event.id,
            "name": event.name,
            "event_type": event.event_type,
            "start_date": event.start_date.isoformat(),
            "end_date": event.end_date.isoformat(),
            "logo": event.logo,
            "level_ids": event.level_ids,
        }
        redis_client.set(key, json.dumps(data), ex=ttl)
        logger.info(f"[REDIS] SET {key}, TTL: {ttl}s")

    @staticmethod
    async def set_json(key: str, value: Any, ex: int | None = None):
        json_value = json.dumps(value, ensure_ascii=False)
        redis_client.set(key, json_value, ex=ex)

    @staticmethod
    async def get_json(key: str) -> Any:
        data = redis_client.get(key)
        if data is None:
            return None
        return json.loads(data)
