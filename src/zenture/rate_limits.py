"""Rate-limit metadata parsed from public API response headers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenture.models import RateLimitInfo

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ("RateLimitInfo", "parse_rate_limit_headers")


def parse_rate_limit_headers(headers: Mapping[str, str]) -> RateLimitInfo:
    """Parse standard and legacy zenture rate-limit headers."""

    normalized = {name.lower(): value for name, value in headers.items()}
    return RateLimitInfo(
        limit=_parse_non_negative_int(
            normalized.get("ratelimit-limit") or normalized.get("x-ratelimit-limit")
        ),
        remaining=_parse_non_negative_int(
            normalized.get("ratelimit-remaining") or normalized.get("x-ratelimit-remaining")
        ),
        reset_after=_parse_non_negative_float(
            normalized.get("ratelimit-reset") or normalized.get("x-ratelimit-reset")
        ),
        retry_after=_parse_non_negative_float(normalized.get("retry-after")),
    )


def _parse_non_negative_int(value: str | None) -> int | None:
    parsed = _parse_non_negative_float(value)
    if parsed is None:
        return None
    if not parsed.is_integer():
        return None
    return int(parsed)


def _parse_non_negative_float(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        parsed = float(value)
    except ValueError:
        return None

    if parsed < 0:
        return None
    return parsed
