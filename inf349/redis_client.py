# inf349/redis_client.py
import os, redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# ❌ retire decode_responses=True
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=False,   # ← impératif : laisser les données en bytes
    health_check_interval=30,
)
