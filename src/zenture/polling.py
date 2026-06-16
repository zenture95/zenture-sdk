"""Operation polling primitives."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import model_validator

from zenture._contract import OperationStatus
from zenture.models import SDKBaseModel

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = (
    "OperationStatus",
    "PollingConfig",
    "is_terminal_status",
    "next_poll_interval",
    "remaining_timeout",
    "should_stop_polling",
)

_TERMINAL_STATUSES = frozenset(
    {
        OperationStatus.SUCCEEDED,
        OperationStatus.FAILED,
        OperationStatus.CANCELLED,
        OperationStatus.EXPIRED,
    }
)


class PollingConfig(SDKBaseModel):
    """Polling timeout and interval policy."""

    timeout: float = 120.0
    initial_interval: float = 1.0
    max_interval: float = 8.0

    @model_validator(mode="after")
    def _validate_intervals(self) -> PollingConfig:
        if self.timeout <= 0:
            raise ValueError("timeout must be positive.")
        if self.initial_interval <= 0:
            raise ValueError("initial_interval must be positive.")
        if self.max_interval < self.initial_interval:
            raise ValueError("max_interval must be greater than or equal to initial_interval.")
        return self


def is_terminal_status(status: OperationStatus | str) -> bool:
    """Return whether an operation status is terminal."""

    return OperationStatus(status) in _TERMINAL_STATUSES


def next_poll_interval(*, current: float, max_interval: float) -> float:
    """Return the next deterministic poll interval, capped at max_interval."""

    doubled = current * 2.0
    if doubled > max_interval:
        return max_interval
    return doubled


def remaining_timeout(*, deadline: float, now: float) -> float:
    """Return remaining seconds in a polling deadline budget."""

    remaining = deadline - now
    if remaining <= 0:
        return 0.0
    return remaining


def should_stop_polling(stop: Callable[[], bool] | None) -> bool:
    """Return whether caller-provided local stop has been requested."""

    if stop is None:
        return False
    return stop()
