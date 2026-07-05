"""
Query complexity classifier.

Phase 1 version: simple heuristics (token count + keyword signals).
Later you can upgrade this to an embedding-based classifier -
but heuristics are a perfectly legitimate v1 and easy to explain
in an interview.
"""

REASONING_KEYWORDS = [
    "explain", "design", "compare", "analyze", "architecture",
    "why", "how does", "trade-off", "tradeoff", "strategy",
    "plan", "optimize", "debug", "write a", "implement",
]


def classify_complexity(prompt: str) -> str:
    """
    Returns "simple" or "complex".
    """
    word_count = len(prompt.split())
    lowered = prompt.lower()

    has_reasoning_signal = any(kw in lowered for kw in REASONING_KEYWORDS)

    if word_count > 25 or has_reasoning_signal:
        return "complex"
    return "simple"
