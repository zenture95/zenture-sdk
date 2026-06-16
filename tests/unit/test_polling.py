"""Operation polling primitives."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

import zenture.polling as polling
from zenture.polling import OperationStatus, PollingConfig, is_terminal_status


def test_terminal_operation_statuses() -> None:
    assert not is_terminal_status(OperationStatus.QUEUED)
    assert not is_terminal_status(OperationStatus.RUNNING)
    assert is_terminal_status(OperationStatus.SUCCEEDED)
    assert is_terminal_status(OperationStatus.FAILED)
    assert is_terminal_status(OperationStatus.CANCELLED)
    assert is_terminal_status(OperationStatus.EXPIRED)


def test_polling_config_is_frozen_pydantic_model() -> None:
    config = PollingConfig(timeout=120.0, initial_interval=1.0, max_interval=8.0)

    assert isinstance(config, BaseModel)
    with pytest.raises(ValidationError):
        config.timeout = 60.0


def test_polling_config_rejects_invalid_intervals() -> None:
    with pytest.raises(ValidationError):
        PollingConfig(timeout=120.0, initial_interval=0.0, max_interval=8.0)

    with pytest.raises(ValidationError):
        PollingConfig(timeout=120.0, initial_interval=9.0, max_interval=8.0)


def test_next_poll_interval_progresses_deterministically_and_caps_at_max() -> None:
    assert polling.next_poll_interval(current=1.0, max_interval=8.0) == 2.0
    assert polling.next_poll_interval(current=4.0, max_interval=8.0) == 8.0
    assert polling.next_poll_interval(current=8.0, max_interval=8.0) == 8.0


def test_remaining_timeout_uses_deadline_budget() -> None:
    assert polling.remaining_timeout(deadline=125.0, now=120.5) == 4.5
    assert polling.remaining_timeout(deadline=125.0, now=126.0) == 0.0


def test_should_stop_polling_honors_optional_stop_callback() -> None:
    assert not polling.should_stop_polling(None)
    assert polling.should_stop_polling(lambda: True)
    assert not polling.should_stop_polling(lambda: False)
