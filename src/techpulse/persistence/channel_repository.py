from dataclasses import dataclass

import redis.asyncio as aioredis


@dataclass(frozen=True)
class ChannelInfo:
    handle: str


# noinspection PyUnresolvedReferences,PyMethodMayBeStatic
class ChannelRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _subs_key(self, user_id: int) -> str:
        return f"subscriptions:{user_id}"

    async def subscribe(self, user_id: int, handle: str) -> None:
        await self._redis.sadd(self._subs_key(user_id), handle)

    async def unsubscribe(self, user_id: int, handle: str) -> None:
        await self._redis.srem(self._subs_key(user_id), handle)

    async def get_subscriptions(self, user_id: int) -> list[ChannelInfo]:
        handles: set[str] = await self._redis.smembers(self._subs_key(user_id))
        return [ChannelInfo(handle=h) for h in sorted(handles)]

    async def is_subscribed(self, user_id: int, handle: str) -> bool:
        return bool(await self._redis.sismember(self._subs_key(user_id), handle))
