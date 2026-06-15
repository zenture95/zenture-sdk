"""Retry policy behavior."""

from __future__ import annotations

from zenture.retries import RetryDecision, should_retry


def test_get_dependency_unavailable_is_retryable_within_attempt_budget() -> None:
    decision = should_retry(
        method="GET",
        status_code=503,
        error_code="dependency_unavailable",
        has_idempotency_key=False,
        attempt=0,
        max_attempts=3,
    )

    assert decision == RetryDecision(retry=True, reason="retryable_status")


def test_mutating_post_without_idempotency_key_is_not_retryable() -> None:
    decision = should_retry(
        method="POST",
        status_code=503,
        error_code="dependency_unavailable",
        has_idempotency_key=False,
        attempt=0,
        max_attempts=3,
    )

    assert decision == RetryDecision(retry=False, reason="missing_idempotency_key")


def test_mutating_post_with_idempotency_key_can_retry_retryable_status() -> None:
    decision = should_retry(
        method="POST",
        status_code=503,
        error_code="capacity_unavailable",
        has_idempotency_key=True,
        attempt=0,
        max_attempts=3,
    )

    assert decision == RetryDecision(retry=True, reason="retryable_status")


def test_non_retryable_validation_errors_do_not_retry() -> None:
    decision = should_retry(
        method="GET",
        status_code=400,
        error_code="validation_failed",
        has_idempotency_key=False,
        attempt=0,
        max_attempts=3,
    )

    assert decision == RetryDecision(retry=False, reason="non_retryable_error")


def test_attempt_budget_stops_retries() -> None:
    decision = should_retry(
        method="GET",
        status_code=429,
        error_code="rate_limited",
        has_idempotency_key=False,
        attempt=3,
        max_attempts=3,
    )

    assert decision == RetryDecision(retry=False, reason="attempt_budget_exhausted")
