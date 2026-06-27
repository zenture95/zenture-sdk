"""Internal contract helpers for public API response headers."""

from __future__ import annotations

from zenture.rate_limits import RateLimitInfo, parse_rate_limit_headers

RATE_LIMIT_HEADER_NAMES = (
    "RateLimit-Limit",
    "RateLimit-Remaining",
    "RateLimit-Reset",
    "Retry-After",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
)

__all__ = ("RATE_LIMIT_HEADER_NAMES", "RateLimitInfo", "parse_rate_limit_headers")
