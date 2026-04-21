import redis.asyncio as aioredis


class ReleaseRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _seen_key(self, user_id: int) -> str:
        return f"seen_releases:{user_id}"

    async def filter_unseen(self, user_id: int, release_ids: list[str]) -> list[str]:
        if not release_ids:
            return []
        results = await self._redis.smismember(self._seen_key(user_id), *release_ids)
        return [rid for rid, seen in zip(release_ids, results) if not seen]

    async def mark_many_seen(self, user_id: int, release_ids: list[str]) -> None:
        if not release_ids:
            return
        await self._redis.sadd(self._seen_key(user_id), *release_ids)
