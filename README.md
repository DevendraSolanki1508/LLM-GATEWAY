# LLM Gateway (Phase 1)

A minimal multi-provider LLM gateway: classifies query complexity, routes to
the right provider, and falls back automatically if one fails.

This is **Phase 1** of the full project — a single working `/chat` endpoint
using Groq (cloud, free tier) and Ollama (local, free) as providers.

## What it does right now

1. You send a prompt to `/chat`
2. The classifier labels it `simple` or `complex`
3. The router tries Groq first; if Groq fails (no key, timeout, rate limit),
   it automatically falls back to your local Ollama model
4. You get back the answer + which provider handled it + latency

## Setup

### 1. Install dependencies
```bash
cd llm-gateway
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get a free Groq API key
Sign up at https://console.groq.com/keys (free, no credit card needed)

### 3. Set your API key
```bash
cp .env.example .env
# then edit .env and paste your key
```

Or just export it directly:
```bash
export GROQ_API_KEY=your_key_here
```

### 4. (Optional) Install Ollama for the local fallback
```bash
# https://ollama.com/download
ollama pull llama3.2:3b
```
If you skip this step, the gateway still works — it'll just fail over to
nothing if Groq fails, and you'll see the actual error message.

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

Server runs at http://localhost:8000

### 6. Test it
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?"}'
```

Try a complex one to see it get classified differently:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain the trade-offs between SQL and NoSQL databases for a high-write system"}'
```

You can also open http://localhost:8000/docs for the interactive Swagger UI.

## Project structure

```
llm-gateway/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── classifier.py         # complexity classifier (simple/complex)
│   ├── router_logic.py       # routing table + fallback logic
│   ├── routers/
│   │   └── chat.py           # /chat endpoint
│   └── providers/
│       ├── base.py           # abstract provider interface
│       ├── groq_provider.py  # Groq API integration
│       └── ollama_provider.py # local Ollama integration
├── requirements.txt
├── .env.example
└── README.md
```

## What's next (Phase 2+)

- [ ] Add Gemini as a third provider
- [ ] Redis exact-match caching
- [ ] Semantic caching with ChromaDB + embeddings
- [ ] Prometheus + Grafana observability
- [ ] Locust load testing
- [ ] Docker + docker-compose
- [ ] Deploy to a public URL
