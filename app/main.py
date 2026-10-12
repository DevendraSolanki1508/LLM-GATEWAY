from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import chat

app = FastAPI(
    title="LLM Gateway",
    description="Multi-provider LLM router with classification, caching, and fallback",
    version="0.1.0",
)

app.include_router(chat.router)

# Exposes generic HTTP metrics automatically (request count, latency, status
# codes) at /metrics, which Prometheus will scrape. Our custom metrics
# (provider usage, cache hit rate) are defined separately in app/metrics.py
# and registered automatically via the same prometheus_client registry.
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    return {"status": "ok", "message": "LLM Gateway is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
