"""Validate built sdist and wheel contents for public release safety."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path


def _one_artifact(dist_dir: Path, pattern: str) -> Path:
    matches = sorted(dist_dir.glob(pattern))
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one {pattern} artifact, found {len(matches)}.")
    return matches[0]


def _tar_names(path: Path) -> set[str]:
    with tarfile.open(path, "r:gz") as archive:
        return set(archive.getnames())


def _zip_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def _has_suffix(names: set[str], suffix: str) -> bool:
    return any(name.endswith(suffix) for name in names)


def _has_prefix(names: set[str], prefix: str) -> bool:
    return any(name.startswith(prefix) for name in names)


def _assert_sdist(path: Path) -> None:
    names = _tar_names(path)
    required_suffixes = [
        "AGENTS.md",
        "README.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "docs/pagination.md",
        "examples/pagination.py",
        "openapi/zenture-public-api-v1.openapi.json",
        "tests/unit/test_docs_examples.py",
        "src/zenture/py.typed",
    ]
    forbidden_suffixes = [
        "PLAN_ZENTURE_SDK.md",
        ".env",
        ".coverage",
    ]

    for suffix in required_suffixes:
        if not _has_suffix(names, suffix):
            raise SystemExit(f"sdist is missing {suffix}.")
    for suffix in forbidden_suffixes:
        if _has_suffix(names, suffix):
            raise SystemExit(f"sdist unexpectedly contains {suffix}.")


def _assert_wheel(path: Path) -> None:
    names = _zip_names(path)
    required = [
        "zenture/__init__.py",
        "zenture/py.typed",
    ]
    forbidden_prefixes = [
        "docs/",
        "examples/",
        "openapi/",
        "tests/",
    ]
    forbidden_suffixes = [
        "AGENTS.md",
        "PLAN_ZENTURE_SDK.md",
    ]

    for file_name in required:
        if file_name not in names:
            raise SystemExit(f"wheel is missing {file_name}.")
    if not any(name.endswith(".dist-info/METADATA") for name in names):
        raise SystemExit("wheel is missing METADATA.")
    for prefix in forbidden_prefixes:
        if _has_prefix(names, prefix):
            raise SystemExit(f"wheel unexpectedly contains {prefix}.")
    for suffix in forbidden_suffixes:
        if _has_suffix(names, suffix):
            raise SystemExit(f"wheel unexpectedly contains {suffix}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist_dir", type=Path)
    args = parser.parse_args()

    dist_dir = args.dist_dir
    if not dist_dir.is_dir():
        raise SystemExit(f"{dist_dir} is not a directory.")

    _assert_sdist(_one_artifact(dist_dir, "*.tar.gz"))
    _assert_wheel(_one_artifact(dist_dir, "*.whl"))


if __name__ == "__main__":
    main()
