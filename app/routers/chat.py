import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.classifier import classify_complexity
from app.router_logic import route_request
from app.providers.base import ProviderError
from app.cache.exact_cache import get_cached, set_cached
from app.cache.semantic_cache import get_semantic_cached, set_semantic_cached

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    text: str
    provider: str
    complexity: str
    latency_ms: float
    total_latency_ms: float
    fallback_used: bool
    skipped_providers: list[str] = []
    cache_hit: bool = False
    cache_type: str = "none"  # "exact" | "semantic" | "none"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start = time.perf_counter()

    # 1. Exact-match cache - cheapest possible path (hash lookup)
    cached = await get_cached(request.prompt)
    if cached is not None:
        total_latency_ms = round((time.perf_counter() - start) * 1000, 2)
        cached["total_latency_ms"] = total_latency_ms
        cached["cache_hit"] = True
        cached["cache_type"] = "exact"
        return ChatResponse(**cached)

    # 2. Semantic cache - catches reworded duplicates (embedding similarity search)
    semantic_hit = await get_semantic_cached(request.prompt)
    if semantic_hit is not None:
        total_latency_ms = round((time.perf_counter() - start) * 1000, 2)
        semantic_hit["total_latency_ms"] = total_latency_ms
        semantic_hit["cache_hit"] = True
        semantic_hit["cache_type"] = "semantic"
        return ChatResponse(**semantic_hit)

    # 3. Cache miss on both - classify and route to a real provider
    complexity = classify_complexity(request.prompt)

    try:
        result = await route_request(request.prompt, complexity)
    except ProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))

    total_latency_ms = round((time.perf_counter() - start) * 1000, 2)

    response = ChatResponse(
        text=result["text"],
        provider=result["provider"],
        complexity=complexity,
        latency_ms=result["latency_ms"],
        total_latency_ms=total_latency_ms,
        fallback_used=result["fallback_used"],
        skipped_providers=result.get("skipped_providers", []),
        cache_hit=False,
        cache_type="none",
    )

    # 4. Store in both caches for next time (fire and forget - best effort)
    response_dict = response.model_dump()
    await set_cached(request.prompt, response_dict)
    await set_semantic_cached(request.prompt, response_dict)

    return response
