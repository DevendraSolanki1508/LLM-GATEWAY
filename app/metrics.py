"""
Custom Prometheus metrics for the gateway.

The prometheus-fastapi-instrumentator library (wired in main.py) already gives
us generic HTTP metrics for free (request count, latency, status codes).
These are the gateway-specific metrics that actually tell the story we want
to show on a dashboard: which provider handled requests, and how effective
the caching layer is.
"""

from prometheus_client import Counter, Histogram

# How many requests each provider actually served
PROVIDER_REQUESTS = Counter(
    "gateway_provider_requests_total",
    "Total requests served by each provider",
    ["provider"],
)

# How many requests were served from cache vs a real provider call,
# broken down by cache type (exact / semantic / none)
CACHE_RESULTS = Counter(
    "gateway_cache_results_total",
    "Cache hit/miss breakdown by cache type",
    ["cache_type"],
)

# How often fallback logic actually had to kick in (primary provider failed)
FALLBACK_EVENTS = Counter(
    "gateway_fallback_total",
    "Number of requests that required falling back from the primary provider",
)

# End-to-end request latency, bucketed - this is what lets you compute
# p50/p95/p99 in Grafana
REQUEST_LATENCY = Histogram(
    "gateway_request_latency_ms",
    "End-to-end request latency in milliseconds",
    ["cache_hit"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000),
)


def record_request(provider: str, cache_type: str, fallback_used: bool, total_latency_ms: float):
       """Call this once per request to update all metrics together."""
       CACHE_RESULTS.labels(cache_type=cache_type).inc()
       # Only real LLM calls count toward provider and fallback metrics;
       # cache hits are already tracked in CACHE_RESULTS.
       if cache_type == "none":
           PROVIDER_REQUESTS.labels(provider=provider).inc()
           if fallback_used:
               FALLBACK_EVENTS.inc()
       REQUEST_LATENCY.labels(cache_hit=str(cache_type != "none")).observe(total_latency_ms)
