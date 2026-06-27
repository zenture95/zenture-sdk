"""Rate-limit header parsing."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from zenture.rate_limits import RateLimitInfo, parse_rate_limit_headers


def test_rate_limit_info_is_a_frozen_pydantic_model() -> None:
    info = RateLimitInfo(limit=100)

    assert isinstance(info, BaseModel)
    with pytest.raises(ValidationError):
        info.limit = 200


def test_rate_limit_info_uses_strict_pydantic_validation() -> None:
    with pytest.raises(ValidationError):
        RateLimitInfo.model_validate({"limit": "100"})


def test_parse_rate_limit_headers_prefers_standard_headers() -> None:
    info = parse_rate_limit_headers(
        {
            "RateLimit-Limit": "100",
            "RateLimit-Remaining": "42",
            "RateLimit-Reset": "9",
            "Retry-After": "3",
            "X-RateLimit-Limit": "10",
        }
    )

    assert info == RateLimitInfo(limit=100, remaining=42, reset_after=9.0, retry_after=3.0)


def test_parse_rate_limit_headers_falls_back_to_legacy_headers() -> None:
    info = parse_rate_limit_headers(
        {
            "X-RateLimit-Limit": "50",
            "X-RateLimit-Remaining": "7",
            "X-RateLimit-Reset": "12",
        }
    )

    assert info == RateLimitInfo(limit=50, remaining=7, reset_after=12.0, retry_after=None)


def test_parse_rate_limit_headers_ignores_invalid_values() -> None:
    info = parse_rate_limit_headers(
        {
            "RateLimit-Limit": "invalid",
            "RateLimit-Remaining": "-1",
            "RateLimit-Reset": "-4",
            "Retry-After": "invalid",
        }
    )

    assert info == RateLimitInfo(limit=None, remaining=None, reset_after=None, retry_after=None)
