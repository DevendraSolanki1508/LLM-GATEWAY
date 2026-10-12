import hashlib
import json
import os

import redis.asyncio as redis

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 3600))

_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=0.5,
    socket_timeout=0.5,
)


def _make_key(prompt: str) -> str:
    normalized = prompt.strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"exact_cache:{digest}"


async def get_cached(prompt: str) -> dict | None:
    try:
        raw = await _client.get(_make_key(prompt))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


async def set_cached(prompt: str, response: dict) -> None:
    try:
        await _client.set(_make_key(prompt), json.dumps(response), ex=CACHE_TTL_SECONDS)
    except Exception:
        pass
