import redis
import os

# Load Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Connect to Redis
redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
