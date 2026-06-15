"""Idempotency key helpers."""

from __future__ import annotations

import pytest

from zenture.idempotency import IdempotencyKeyError, idempotency_key, validate_idempotency_key


def test_idempotency_key_is_stable_and_sanitized() -> None:
    first = idempotency_key("Customer 123", "chat run", "Request 001")
    second = idempotency_key("Customer 123", "chat run", "Request 001")

    assert first == second
    assert first == "customer-123-chat-run-request-001"


def test_validate_idempotency_key_accepts_safe_key() -> None:
    assert validate_idempotency_key("customer-123-chat-run-request-001") == (
        "customer-123-chat-run-request-001"
    )
    assert validate_idempotency_key("a" * 255) == "a" * 255


def test_validate_idempotency_key_rejects_empty_or_oversized_key() -> None:
    with pytest.raises(IdempotencyKeyError):
        validate_idempotency_key("")

    with pytest.raises(IdempotencyKeyError):
        validate_idempotency_key("a" * 256)


def test_validate_idempotency_key_rejects_unsafe_characters() -> None:
    with pytest.raises(IdempotencyKeyError):
        validate_idempotency_key("customer 123/chat")
