"""
Semantic cache using ChromaDB + sentence-transformers.

Unlike exact_cache (hash-based, catches literal duplicates), this catches
*reworded* duplicates: "What is 2+2?" vs "what's 2 plus 2?" vs "calculate 2+2"
all map to nearly the same embedding vector, so this cache can serve a cached
answer even though the text differs.

Design notes:
- The embedding model loads once at import time (a few hundred MB, local, free).
- ChromaDB persists to disk so the cache survives restarts.
- SIMILARITY_THRESHOLD controls how "close" two prompts must be to count as
  the same question. 0.92 is a reasonably strict default - tune this based
  on false-positive rate you observe (too low = wrong answers served from
  cache; too high = misses that should have hit).
"""

import json
import os

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_cache")
SIMILARITY_THRESHOLD = float(os.environ.get("SEMANTIC_CACHE_THRESHOLD", 0.92))
COLLECTION_NAME = "semantic_cache"

# Loaded once per process - this is the "cost" of semantic caching, paid once,
# not per-request.
_embedder = SentenceTransformer("all-MiniLM-L6-v2")

_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def _embed(text: str) -> list[float]:
    return _embedder.encode(text.strip().lower()).tolist()


async def get_semantic_cached(prompt: str) -> dict | None:
    """
    Returns the cached response dict for the closest sufficiently-similar
    prior prompt, or None if nothing is close enough.
    """
    try:
        if _collection.count() == 0:
            return None

        query_embedding = _embed(prompt)
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
        )

        if not results["ids"][0]:
            return None

        # ChromaDB returns cosine *distance* (0 = identical, 2 = opposite).
        # Convert to similarity: similarity = 1 - distance
        distance = results["distances"][0][0]
        similarity = 1 - distance

        if similarity < SIMILARITY_THRESHOLD:
            return None

        stored_response = results["metadatas"][0][0]["response"]
        return json.loads(stored_response)
    except Exception:
        # Best-effort - never let the semantic cache break the request path
        return None


async def set_semantic_cached(prompt: str, response: dict) -> None:
    """Stores the prompt's embedding + response for future semantic lookups."""
    try:
        embedding = _embed(prompt)
        # Use the prompt itself as a simple unique ID (good enough for this scale)
        doc_id = str(hash(prompt.strip().lower()))

        _collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[{"response": json.dumps(response), "original_prompt": prompt}],
        )
    except Exception:
        pass
