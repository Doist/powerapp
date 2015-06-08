"""
Utilities to work with Redis. Currently consists just of a Redis pool (one per
thread) and a function returning the Redis client using this pool
"""
import redis
from django.conf import settings
from redis.lock import LuaLock

pool = redis.ConnectionPool.from_url(settings.REDIS_URL)


def get_redis():
    return redis.StrictRedis(connection_pool=pool)
