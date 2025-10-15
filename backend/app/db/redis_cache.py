# agenticAI/backend/app/db/redis_cache.py

"""
Redis Cache Manager with Hot Reload Mechanism

This module provides:
1. Redis connection management
2. Cache operations (get, set, delete)
3. Hot reload mechanism (periodically sync from PostgreSQL to local cache)
4. Fallback to database when Redis is unavailable

Cache Strategy:
- Frequently accessed data is cached in Redis
- Local in-memory fallback for development
- Automatic cache invalidation after TTL
- Hot reload refreshes cache from PostgreSQL every N minutes
"""

import asyncio
import json
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


# =============================================================================
# REDIS CONNECTION MANAGEMENT
# =============================================================================
class RedisCache:
    """
    Redis cache manager with async operations and hot reload.
    
    Features:
    - Async Redis operations
    - Connection pooling
    - Automatic reconnection
    - Fallback to in-memory cache if Redis unavailable
    - Hot reload mechanism from PostgreSQL
    """
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self._local_cache: dict[str, Any] = {}  # Fallback in-memory cache
        self._hot_reload_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """
        Connect to Redis server.
        
        If connection fails, logs error and falls back to in-memory cache.
        """
        if not settings.ENABLE_CACHE:
            log.info("Redis caching disabled")
            return
        
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,  # Connection pool size
            )
            
            # Test connection
            await self.redis_client.ping()
            log.info("Redis connection established", url=settings.REDIS_HOST)
            
            # Start hot reload task
            if settings.CACHE_HOT_RELOAD_INTERVAL > 0:
                self._hot_reload_task = asyncio.create_task(self._hot_reload_loop())
                log.info("Hot reload mechanism started", interval=settings.CACHE_HOT_RELOAD_INTERVAL)
        
        except Exception as e:
            log.warning(
                "Redis connection failed, using in-memory cache",
                exc_info=e
            )
            self.redis_client = None
    
    async def disconnect(self) -> None:
        """Close Redis connection and stop hot reload."""
        if self._hot_reload_task:
            self._hot_reload_task.cancel()
            try:
                await self._hot_reload_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
            log.info("Redis connection closed")
    
    # =========================================================================
    # CACHE OPERATIONS
    # =========================================================================
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Fallback to in-memory cache
                return self._local_cache.get(key)
        except Exception as e:
            log.warning("Cache get failed", key=key, exc_info=e)
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (default: from settings)
        
        Returns:
            True if successful, False otherwise
        """
        ttl = ttl or settings.CACHE_TTL
        
        try:
            serialized = json.dumps(value)
            
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                # Fallback to in-memory cache (no TTL in fallback)
                self._local_cache[key] = value
            
            return True
        
        except Exception as e:
            log.warning("Cache set failed", key=key, exc_info=e)
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self._local_cache.pop(key, None)
            
            return True
        
        except Exception as e:
            log.warning("Cache delete failed", key=key, exc_info=e)
            return False
    
    async def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.redis_client:
                await self.redis_client.flushdb()
            else:
                self._local_cache.clear()
            
            log.info("Cache cleared")
            return True
        
        except Exception as e:
            log.error("Cache clear failed", exc_info=e)
            return False
    
    # =========================================================================
    # HOT RELOAD MECHANISM
    # =========================================================================
    
    async def _hot_reload_loop(self) -> None:
        """
        Background task to periodically reload cache from PostgreSQL.
        
        This ensures cache stays fresh with database changes made by other services.
        """
        while True:
            try:
                await asyncio.sleep(settings.CACHE_HOT_RELOAD_INTERVAL)
                await self._reload_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Hot reload failed", exc_info=e)
    
    async def _reload_cache(self) -> None:
        """
        Reload frequently accessed data from PostgreSQL to cache.
        
        TODO: In Step 1.4, this will reload:
        - Recent conversation summaries
        - Agent performance metrics
        - User preferences
        """
        log.debug("Hot reload triggered")
        
        # TODO: Implement actual reload logic in Step 1.4
        # Example:
        # async with get_db_session() as db:
        #     conversations = await db.execute(select(Conversation).limit(100))
        #     for conv in conversations.scalars():
        #         await self.set(f"conv:{conv.id}", conv.dict())


# =============================================================================
# GLOBAL CACHE INSTANCE
# =============================================================================
cache = RedisCache()


async def init_cache() -> None:
    """Initialize Redis cache. Call at application startup."""
    await cache.connect()


async def close_cache() -> None:
    """Close Redis cache. Call at application shutdown."""
    await cache.disconnect()