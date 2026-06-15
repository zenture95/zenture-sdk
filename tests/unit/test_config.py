"""Configuration model behavior."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from zenture.config import ZentureConfig, load_config_from_env
from zenture.redaction import REDACTED


def test_config_is_frozen_pydantic_model_and_redacts_api_key() -> None:
    config = ZentureConfig(api_key="zt_test_config_123")

    assert isinstance(config, BaseModel)
    assert config.base_url == "https://api.zenture.app"
    assert config.api_base_url == "https://api.zenture.app/v1"
    assert config.connect_timeout == 5.0
    assert config.read_timeout == 30.0
    assert config.write_timeout == 30.0
    assert config.pool_timeout == 30.0
    assert config.max_retries == 2
    assert config.initial_retry_backoff == 0.5
    assert config.max_retry_backoff == 8.0
    assert "zt_test_config_123" not in repr(config)
    assert REDACTED in repr(config)
    with pytest.raises(ValidationError):
        config.base_url = "https://api-int.zenture.app"


def test_config_accepts_timeout_and_retry_overrides() -> None:
    config = ZentureConfig(
        api_key="zt_test_config_123",
        connect_timeout=1.0,
        read_timeout=2.0,
        write_timeout=3.0,
        pool_timeout=4.0,
        max_retries=4,
        initial_retry_backoff=0.2,
        max_retry_backoff=1.0,
    )

    assert config.connect_timeout == 1.0
    assert config.read_timeout == 2.0
    assert config.write_timeout == 3.0
    assert config.pool_timeout == 4.0
    assert config.max_retries == 4


def test_config_rejects_invalid_timeout_and_retry_policy() -> None:
    with pytest.raises(ValidationError):
        ZentureConfig(api_key="zt_test_config_123", connect_timeout=0.0)
    with pytest.raises(ValidationError):
        ZentureConfig(api_key="zt_test_config_123", max_retries=-1)
    with pytest.raises(ValidationError):
        ZentureConfig(
            api_key="zt_test_config_123",
            initial_retry_backoff=2.0,
            max_retry_backoff=1.0,
        )


def test_config_rejects_api_key_with_surrounding_whitespace() -> None:
    with pytest.raises(ValidationError):
        ZentureConfig(api_key=" zt_test_config_123 ")


def test_config_accepts_only_official_int_and_local_origins() -> None:
    config = ZentureConfig(api_key="zt_test_config_123", base_url="https://api-int.zenture.app/")

    assert config.base_url == "https://api-int.zenture.app"

    with pytest.raises(ValidationError):
        ZentureConfig(api_key="zt_test_config_123", base_url="https://api.zenture.app/v1")

    with pytest.raises(ValidationError):
        ZentureConfig(api_key="zt_test_config_123", base_url="https://evil.example")


def test_config_rejects_base_url_credentials_even_for_local_debugging() -> None:
    with pytest.raises(ValidationError):
        ZentureConfig(
            api_key="zt_test_config_123",
            base_url="http://user:password@localhost:8000",
        )


def test_config_allows_local_http_only_for_local_debugging() -> None:
    assert (
        ZentureConfig(api_key="zt_test_config_123", base_url="http://localhost:8000").api_base_url
        == "http://localhost:8000/v1"
    )

    with pytest.raises(ValidationError):
        ZentureConfig(api_key="zt_test_config_123", base_url="http://example.com")


def test_load_config_from_env_reads_api_key_and_optional_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ZENTURE_API_KEY", "zt_test_config_env")
    monkeypatch.setenv("ZENTURE_BASE_URL", "https://api-int.zenture.app")

    config = load_config_from_env()

    assert config.api_key_value == "zt_test_config_env"
    assert config.base_url == "https://api-int.zenture.app"


def test_load_config_from_env_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZENTURE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ZENTURE_API_KEY"):
        load_config_from_env()
