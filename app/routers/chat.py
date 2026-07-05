import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.classifier import classify_complexity
from app.router_logic import route_request
from app.providers.base import ProviderError

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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start = time.perf_counter()

    complexity = classify_complexity(request.prompt)

    try:
        result = await route_request(request.prompt, complexity)
    except ProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))

    total_latency_ms = round((time.perf_counter() - start) * 1000, 2)

    return ChatResponse(
        text=result["text"],
        provider=result["provider"],
        complexity=complexity,
        latency_ms=result["latency_ms"],
        total_latency_ms=total_latency_ms,
        fallback_used=result["fallback_used"],
        skipped_providers=result.get("skipped_providers", []),
    )
