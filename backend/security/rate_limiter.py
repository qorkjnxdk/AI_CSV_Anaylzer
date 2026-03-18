import logging
import math
import time
from collections import defaultdict
from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error")


class RateLimiter:
    def __init__(self):
        # key -> list of timestamps
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int):
        """Raise HTTP 429 if key has exceeded max_requests in the last window_seconds."""
        now = time.time()
        cutoff = now - window_seconds
        # Prune old entries
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]
        logger.info("[RATE LIMIT] key=%s hits=%d/%d", key, len(self._hits[key]), max_requests)
        if len(self._hits[key]) >= max_requests:
            # Earliest hit expires at hits[0] + window_seconds
            retry_after = math.ceil(self._hits[key][0] + window_seconds - now)
            raise HTTPException(
                status_code=429,
                detail={
                    "message": f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s.",
                    "retry_after": retry_after,
                },
            )
        self._hits[key].append(now)


limiter = RateLimiter()
