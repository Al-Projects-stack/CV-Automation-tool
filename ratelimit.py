"""Lightweight in-memory per-key rate limiter.

Sized for a single-instance deployment (Render free tier). If the app is ever
scaled to multiple workers/instances, replace this with a shared store (Redis).
"""
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

# Defaults: 10 requests per 60s window per key. Override via env.
_MAX = int(os.environ.get("RATE_LIMIT_MAX", "10"))
_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))

_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def enforce(key: str, max_requests: int = _MAX, window: int = _WINDOW) -> None:
    """Raise HTTP 429 if `key` has exceeded `max_requests` within `window` seconds."""
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        cutoff = now - window
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= max_requests:
            retry_after = int(q[0] + window - now) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait a moment and try again.",
                headers={"Retry-After": str(retry_after)},
            )
        q.append(now)
