from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from app.routers import chat

app = FastAPI(
    title="LLM Gateway",
    description="Multi-provider LLM router with classification and fallback",
    version="0.1.0",
)

app.include_router(chat.router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "LLM Gateway is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}