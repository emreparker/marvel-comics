"""API middleware for rate limiting."""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Token bucket rate limiter by IP address."""

    def __init__(self, requests_per_minute: int = 60, burst: int = 30):
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.burst = burst
        self.buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (burst, time.time())
        )

    def is_allowed(self, ip: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.

        Returns:
            (allowed, remaining, reset_seconds)
        """
        tokens, last_time = self.buckets[ip]
        now = time.time()

        # Add tokens based on time elapsed
        elapsed = now - last_time
        tokens = min(self.burst, tokens + elapsed * self.rate)

        if tokens >= 1:
            # Allow request, consume token
            tokens -= 1
            self.buckets[ip] = (tokens, now)
            return True, int(tokens), 0
        else:
            # Deny request
            reset_seconds = int((1 - tokens) / self.rate)
            self.buckets[ip] = (tokens, now)
            return False, 0, reset_seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that applies rate limiting to all requests."""

    def __init__(self, app, requests_per_minute: int = 60, burst: int = 30):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, burst)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client IP
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        # Check rate limit
        allowed, remaining, reset = self.limiter.is_allowed(ip)

        if not allowed:
            return Response(
                content='{"detail": "Rate limit exceeded. Please wait before making more requests."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
