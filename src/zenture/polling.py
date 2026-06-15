"""Operation polling primitives."""

from __future__ import annotations

from pydantic import model_validator

from zenture._contract import OperationStatus
from zenture.models import SDKBaseModel

__all__ = ("OperationStatus", "PollingConfig", "is_terminal_status")

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
