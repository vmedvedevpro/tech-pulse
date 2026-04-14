import redis.asyncio as aioredis


# noinspection PyUnresolvedReferences
async def create_redis(url: str) -> aioredis.Redis:
    client = aioredis.from_url(url, decode_responses=True)
    await client.ping()
    return client
