"""Configuration model behavior."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from zenture.config import ZentureConfig, load_config_from_env
from zenture.redaction import REDACTED


def test_config_is_frozen_pydantic_model_and_redacts_api_key() -> None:
    config = ZentureConfig(api_key="zt_live_config_123")

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
    assert "zt_live_config_123" not in repr(config)
    assert REDACTED in repr(config)
    with pytest.raises(ValidationError):
        config.base_url = "https://api-example.zenture.app"


def test_config_accepts_timeout_and_retry_overrides() -> None:
    config = ZentureConfig(
        api_key="zt_live_config_123",
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
        ZentureConfig(api_key="zt_live_config_123", connect_timeout=0.0)
    with pytest.raises(ValidationError):
        ZentureConfig(api_key="zt_live_config_123", max_retries=-1)
    with pytest.raises(ValidationError):
        ZentureConfig(
            api_key="zt_live_config_123",
            initial_retry_backoff=2.0,
            max_retry_backoff=1.0,
        )


def test_config_rejects_api_key_with_surrounding_whitespace() -> None:
    with pytest.raises(ValidationError):
        ZentureConfig(api_key=" zt_test_config_123 ")


def test_live_token_defaults_to_production_and_rejects_non_production_origins() -> None:
    config = ZentureConfig(api_key="zt_live_config_123")

    assert config.base_url == "https://api.zenture.app"
    assert config.api_base_url == "https://api.zenture.app/v1"

    with pytest.raises(ValidationError, match="Live API tokens"):
        ZentureConfig(api_key="zt_live_config_123", base_url="https://api-staging.zenture.app")

    with pytest.raises(ValidationError, match="Live API tokens"):
        ZentureConfig(api_key="zt_live_config_123", base_url="http://localhost:8000")


def test_test_token_requires_explicit_non_production_origin() -> None:
    with pytest.raises(ValidationError, match="Test API tokens require"):
        ZentureConfig(api_key="zt_test_config_123")

    with pytest.raises(ValidationError, match="Test API tokens cannot"):
        ZentureConfig(api_key="zt_test_config_123", base_url="https://api.zenture.app")


def test_test_token_accepts_local_and_zenture_owned_non_production_api_origins() -> None:
    remote = ZentureConfig(
        api_key="zt_test_config_123",
        base_url="https://api-staging.zenture.app/",
    )
    local = ZentureConfig(
        api_key="zt_test_config_123",
        base_url="http://localhost:8000",
    )

    assert remote.base_url == "https://api-staging.zenture.app"
    assert local.api_base_url == "http://localhost:8000/v1"

    with pytest.raises(ValidationError):
        ZentureConfig(api_key="zt_test_config_123", base_url="https://www.zenture.app")


def test_config_rejects_unknown_api_token_prefix() -> None:
    with pytest.raises(ValidationError, match="api_key must start"):
        ZentureConfig(api_key="zt_preview_config_123")


def test_base_url_validation_errors_do_not_disclose_internal_origins() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ZentureConfig(api_key="zt_test_config_123", base_url="https://evil.example")

    message = str(exc_info.value)
    assert "api-example" not in message
    assert "localhost:8000" not in message


def test_config_accepts_only_approved_non_production_and_local_origins() -> None:
    config = ZentureConfig(
        api_key="zt_test_config_123", base_url="https://api-example.zenture.app/"
    )

    assert config.base_url == "https://api-example.zenture.app"

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
    monkeypatch.setenv("ZENTURE_BASE_URL", "https://api-example.zenture.app")

    config = load_config_from_env()

    assert config.api_key_value == "zt_test_config_env"
    assert config.base_url == "https://api-example.zenture.app"


def test_load_config_from_env_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZENTURE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ZENTURE_API_KEY"):
        load_config_from_env()
