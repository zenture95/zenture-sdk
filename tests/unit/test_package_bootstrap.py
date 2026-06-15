"""Package bootstrap tests for the prerelease SDK foundation."""

from __future__ import annotations

import tomllib
from importlib.resources import files
from importlib.util import find_spec
from pathlib import Path

import zenture


def test_package_exposes_version() -> None:
    assert isinstance(zenture.__version__, str)
    assert zenture.__version__
    assert zenture.__version__ != "0.0.0"
    assert zenture.__version__ in Path("CHANGELOG.md").read_text(encoding="utf-8")


def test_public_exports_are_intentionally_minimal_for_first_client_cut() -> None:
    assert zenture.__all__ == ("AsyncZenture", "Zenture", "__version__")
    assert hasattr(zenture, "Zenture")
    assert hasattr(zenture, "AsyncZenture")
    assert not hasattr(zenture, "PublicOperationResponse")


def test_runtime_implementation_modules_are_private() -> None:
    assert find_spec("zenture.transport") is None
    assert find_spec("zenture.resources") is None
    assert find_spec("zenture._transport") is not None
    assert find_spec("zenture._resources") is not None


def test_package_declares_typing_support() -> None:
    assert files("zenture").joinpath("py.typed").is_file()


def test_sdist_includes_openapi_artifact_for_contract_tests() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    sdist_includes = pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]

    assert "/tests" in sdist_includes
    assert "/openapi" in sdist_includes
    assert "/PLAN_ZENTURE_SDK.md" not in sdist_includes


def test_ci_enforces_coverage_gate_and_python_313() -> None:
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert '"3.13"' in ci
    assert "python -m coverage run -m pytest" in ci
    assert "python -m coverage report" in ci
