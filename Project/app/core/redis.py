"""Redis 连接管理"""
import redis.asyncio as aioredis
from app.core.config import settings
from loguru import logger

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 连接（单例）"""
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await _redis.ping()
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            raise
    return _redis


async def close_redis():
    """关闭 Redis 连接"""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
