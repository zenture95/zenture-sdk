"""Helpers for safe idempotency-key handling."""

from __future__ import annotations

import re

MAX_IDEMPOTENCY_KEY_LENGTH = 255
_SAFE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
_UNSAFE_SEGMENT_CHARS = re.compile(r"[^A-Za-z0-9._:-]+")


class IdempotencyKeyError(ValueError):
    """Raised when an idempotency key is empty, too long, or unsafe."""


def idempotency_key(*parts: object) -> str:
    """Build a stable retry-safety key from caller-owned identifiers.

    Use one key per logical mutation and reuse the same key when retrying the
    same request. Good parts are stable ids from your system, such as
    ``("support-ticket-123-answer-a", "evaluate", "v1")`` or
    ``("case-123", "chat-turn-2", "v1")``.

    Do not include prompts, answers, API tokens, raw request bodies, secrets, or
    customer PII in idempotency keys. For external evaluations, this key is
    required retry protection; ``external_id`` is only optional correlation.
    """

    normalized = [_normalize_part(str(part)) for part in parts]
    key = "-".join(part for part in normalized if part)
    return validate_idempotency_key(key)


def validate_idempotency_key(key: str) -> str:
    """Validate and return a caller-provided idempotency key.

    The public API requires this value on mutating async routes including chat,
    evaluation, and input wizard. The same key with the same body is a safe
    retry; the same key with a different body is an idempotency conflict.
    """

    if not key:
        raise IdempotencyKeyError("Idempotency key must not be empty.")
    if len(key) > MAX_IDEMPOTENCY_KEY_LENGTH:
        raise IdempotencyKeyError("Idempotency key is too long.")
    if _SAFE_KEY_PATTERN.fullmatch(key) is None:
        raise IdempotencyKeyError("Idempotency key contains unsafe characters.")
    return key


def _normalize_part(part: str) -> str:
    normalized = _UNSAFE_SEGMENT_CHARS.sub("-", part.strip().lower())
    return normalized.strip("-")
