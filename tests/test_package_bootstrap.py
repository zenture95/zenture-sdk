"""Package bootstrap tests for the prerelease SDK foundation."""

from __future__ import annotations

from importlib.resources import files

import zenture


def test_package_exposes_version() -> None:
    assert isinstance(zenture.__version__, str)
    assert zenture.__version__


def test_public_exports_are_intentionally_minimal_before_runtime_sdk() -> None:
    assert zenture.__all__ == ("__version__",)
    assert not hasattr(zenture, "Zenture")
    assert not hasattr(zenture, "AsyncZenture")


def test_package_declares_typing_support() -> None:
    assert files("zenture").joinpath("py.typed").is_file()
