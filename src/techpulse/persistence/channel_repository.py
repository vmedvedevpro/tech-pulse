from dataclasses import dataclass

import redis.asyncio as aioredis


@dataclass(frozen=True)
class ChannelInfo:
    channel_id: str
    name: str


class ChannelRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _subs_key(self, user_id: int) -> str:
        return f"subscriptions:{user_id}"

    def _channel_name_key(self, channel_id: str) -> str:
        return f"channel:{channel_id}:name"

    async def subscribe(self, user_id: int, channel_id: str, channel_name: str) -> None:
        async with self._redis.pipeline() as pipe:
            pipe.sadd(self._subs_key(user_id), channel_id)
            pipe.set(self._channel_name_key(channel_id), channel_name)
            await pipe.execute()

    async def unsubscribe(self, user_id: int, channel_id: str) -> None:
        await self._redis.srem(self._subs_key(user_id), channel_id)

    async def get_subscriptions(self, user_id: int) -> list[ChannelInfo]:
        channel_ids: set[str] = await self._redis.smembers(self._subs_key(user_id))
        if not channel_ids:
            return []
        sorted_ids = sorted(channel_ids)
        names = await self._redis.mget(*[self._channel_name_key(cid) for cid in sorted_ids])
        return [
            ChannelInfo(channel_id=cid, name=name or cid)
            for cid, name in zip(sorted_ids, names)
        ]

    async def is_subscribed(self, user_id: int, channel_id: str) -> bool:
        return bool(await self._redis.sismember(self._subs_key(user_id), channel_id))
