# utils/redis_utils.py
import redis
import json
from datetime import timedelta
from .Imports import *

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

async def get_cached_data(key):
    """Получить данные из кэша"""
    data = redis_client.get(key)
    return json.loads(data) if data else None

async def set_cached_data(key, data, ttl=None):
    """Сохранить данные в кэш"""
    if ttl:
        redis_client.setex(key, timedelta(seconds=ttl), json.dumps(data))
    else:
        redis_client.set(key, json.dumps(data))

async def invalidate_cache(key):
    """Удалить данные из кэша"""
    redis_client.delete(key)


