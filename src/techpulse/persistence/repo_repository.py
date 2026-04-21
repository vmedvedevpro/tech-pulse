import redis.asyncio as aioredis


class RepoRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _repos_key(self, user_id: int) -> str:
        return f"repos:{user_id}"

    async def add_repo(self, user_id: int, repo: str) -> None:
        await self._redis.sadd(self._repos_key(user_id), repo)

    async def remove_repo(self, user_id: int, repo: str) -> None:
        await self._redis.srem(self._repos_key(user_id), repo)

    async def get_repos(self, user_id: int) -> list[str]:
        repos: set[str] = await self._redis.smembers(self._repos_key(user_id))
        return sorted(repos)

    async def has_repo(self, user_id: int, repo: str) -> bool:
        return bool(await self._redis.sismember(self._repos_key(user_id), repo))
