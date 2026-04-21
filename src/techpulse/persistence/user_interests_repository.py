import redis.asyncio as aioredis


# noinspection PyUnresolvedReferences,PyMethodMayBeStatic
class InterestsRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _interests_key(self, user_id: int) -> str:
        return f"interests:{user_id}"

    async def add_interest(self, user_id: int, interest: str) -> None:
        await self._redis.sadd(self._interests_key(user_id), interest)

    async def remove_interest(self, user_id: int, interest: str) -> None:
        await self._redis.srem(self._interests_key(user_id), interest)

    async def get_interests(self, user_id: int) -> list[str]:
        interests: set[str] = await self._redis.smembers(self._interests_key(user_id))
        return sorted(interests)

    async def has_interest(self, user_id: int, interest: str) -> bool:
        return bool(await self._redis.sismember(self._interests_key(user_id), interest))
