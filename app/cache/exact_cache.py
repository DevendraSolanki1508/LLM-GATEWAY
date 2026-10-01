"""
Exact-match cache using Redis.

Key design: hash the prompt (+ complexity) so keys stay short and fixed-length,
regardless of how long the actual prompt is.
"""

import hashlib
import json
import os

import redis.asyncio as redis

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 3600))  # 1 hour default

_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def _make_key(prompt: str) -> str:
    normalized = prompt.strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"exact_cache:{digest}"


async def get_cached(prompt: str) -> dict | None:
    """Returns cached response dict if found, else None."""
    try:
        key = _make_key(prompt)
        raw = await _client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


async def set_cached(prompt: str, response: dict) -> None:
    """Stores a response dict in the cache with a TTL."""
    try:
        key = _make_key(prompt)
        await _client.set(key, json.dumps(response), ex=CACHE_TTL_SECONDS)
    except Exception:
        pass