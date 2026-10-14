import re

REASONING_KEYWORDS = [
    "explain", "design", "compare", "analyze", "architecture",
    "why", "how does", "trade-off", "tradeoff", "strategy",
    "plan", "optimize", "debug", "write a", "implement",
]


def classify_complexity(prompt: str) -> str:
    word_count = len(prompt.split())
    lowered = prompt.lower()
    # Whole-word matching so "plan" doesn't match "planet"
    has_reasoning_signal = any(
        re.search(rf"\b{re.escape(kw)}\b", lowered) for kw in REASONING_KEYWORDS
    )
    if word_count > 25 or has_reasoning_signal:
        return "complex"
    return "simple"