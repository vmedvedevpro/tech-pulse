import redis.asyncio as aioredis


class VideoRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _seen_key(self, user_id: int) -> str:
        return f"seen_videos:{user_id}"

    async def filter_unseen(self, user_id: int, video_ids: list[str]) -> list[str]:
        if not video_ids:
            return []
        results = await self._redis.smismember(self._seen_key(user_id), *video_ids)
        return [vid for vid, seen in zip(video_ids, results) if not seen]

    async def mark_many_seen(self, user_id: int, video_ids: list[str]) -> None:
        if not video_ids:
            return
        await self._redis.sadd(self._seen_key(user_id), *video_ids)
