"""Configuration for zenture SDK runtime primitives."""

from __future__ import annotations

import os
from typing import Self
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, computed_field, field_validator, model_validator

from zenture.models import SDKBaseModel
from zenture.redaction import REDACTED

DEFAULT_BASE_URL = "https://api.zenture.app"
INT_BASE_URL = "https://api-int.zenture.app"
API_VERSION_PATH = "/v1"
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 30.0
DEFAULT_WRITE_TIMEOUT = 30.0
DEFAULT_POOL_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_INITIAL_RETRY_BACKOFF = 0.5
DEFAULT_MAX_RETRY_BACKOFF = 8.0
_ALLOWED_REMOTE_BASE_URLS = frozenset({DEFAULT_BASE_URL, INT_BASE_URL})
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class ZentureConfig(SDKBaseModel):
    """Validated SDK configuration."""

    api_key: str = Field(repr=False)
    base_url: str = DEFAULT_BASE_URL
    connect_timeout: float = Field(default=DEFAULT_CONNECT_TIMEOUT, gt=0)
    read_timeout: float = Field(default=DEFAULT_READ_TIMEOUT, gt=0)
    write_timeout: float = Field(default=DEFAULT_WRITE_TIMEOUT, gt=0)
    pool_timeout: float = Field(default=DEFAULT_POOL_TIMEOUT, gt=0)
    max_retries: int = Field(default=DEFAULT_MAX_RETRIES, ge=0, le=10)
    initial_retry_backoff: float = Field(default=DEFAULT_INITIAL_RETRY_BACKOFF, ge=0)
    max_retry_backoff: float = Field(default=DEFAULT_MAX_RETRY_BACKOFF, ge=0)

    @field_validator("api_key", mode="before")
    @classmethod
    def _validate_api_key(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("api_key must not be empty.")
        if value != value.strip():
            raise ValueError("api_key must not include surrounding whitespace.")
        return value

    @field_validator("base_url", mode="before")
    @classmethod
    def _validate_base_url(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("base_url must not be empty.")

        parsed = urlsplit(value.strip())
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("base_url must use http or https.")
        if not parsed.netloc:
            raise ValueError("base_url must include a host.")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("base_url must not include credentials.")
        if parsed.query or parsed.fragment:
            raise ValueError("base_url must not include query strings or fragments.")

        hostname = parsed.hostname or ""
        is_local = hostname in _LOCAL_HOSTS
        if parsed.scheme == "http" and not is_local:
            raise ValueError("http base_url is allowed only for local debugging.")

        path = parsed.path.rstrip("/")
        if path:
            raise ValueError("base_url must be an origin without a path.")

        normalized = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        if not is_local and normalized not in _ALLOWED_REMOTE_BASE_URLS:
            raise ValueError(
                "base_url must be the official production, INT, or local debugging origin."
            )

        return normalized

    @model_validator(mode="after")
    def _validate_retry_backoff(self) -> Self:
        if self.max_retry_backoff < self.initial_retry_backoff:
            raise ValueError(
                "max_retry_backoff must be greater than or equal to initial_retry_backoff."
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def api_base_url(self) -> str:
        """Versioned public API base URL."""

        return f"{self.base_url}{API_VERSION_PATH}"

    @property
    def api_key_value(self) -> str:
        """Raw API key for Authorization headers."""

        return self.api_key

    def __repr__(self) -> str:
        return f"ZentureConfig(api_key='{REDACTED}', base_url={self.base_url!r})"

    def __str__(self) -> str:
        return repr(self)

    @classmethod
    def from_env(cls) -> ZentureConfig:
        """Load config from supported environment variables."""

        return load_config_from_env()


def load_config_from_env() -> ZentureConfig:
    """Load SDK config from environment variables."""

    api_key = os.environ.get("ZENTURE_API_KEY")
    if api_key is None or not api_key.strip():
        raise RuntimeError("ZENTURE_API_KEY is required.")

    base_url = os.environ.get("ZENTURE_BASE_URL", DEFAULT_BASE_URL)
    return ZentureConfig(api_key=api_key, base_url=base_url)
