import json
from .redis_client import redis_client


async def cache_message(chat_id: int, message: dict):
    # Save message to Redis cache
    redis_key = f"chat:{chat_id}:messages"
    redis_client.lpush(redis_key, json.dumps(message))
    redis_client.ltrim(redis_key, 0, 49)


async def get_cached_messages(chat_id: int):
    # Retrieve cached messages from Redis
    redis_key = f"chat:{chat_id}:messages"
    messages = redis_client.lrange(redis_key, 0, -1)
    return [json.loads(msg) for msg in messages]
