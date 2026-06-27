# Third-Party Notices

This document summarizes third-party software used by the zenture Python SDK.
It is provided for release transparency and does not replace the upstream
license files or metadata published by each project.

## Runtime Dependencies

These packages are installed for normal SDK use.

| Package | License | Notes |
| --- | --- | --- |
| `httpx` | BSD-3-Clause | Direct HTTP client dependency. |
| `pydantic` | MIT | Direct data validation/model dependency. |
| `httpcore` | BSD-3-Clause | Transitive dependency of `httpx`. |
| `anyio` | MIT | Transitive dependency of `httpx`. |
| `certifi` | MPL-2.0 | Transitive dependency of `httpx`; provides CA certificates. |
| `h11` | MIT | Transitive dependency of `httpcore`. |
| `idna` | BSD-3-Clause | Transitive dependency of `httpx`. |
| `annotated-types` | MIT | Transitive dependency of `pydantic`. |
| `pydantic-core` | MIT | Transitive dependency of `pydantic`. |
| `typing-extensions` | PSF-2.0 | Transitive dependency of `pydantic`. |
| `typing-inspection` | MIT | Transitive dependency of `pydantic`. |

## Build Dependencies

These packages are used to build source distributions and wheels.

| Package | License | Notes |
| --- | --- | --- |
| `hatchling` | MIT | PEP 517 build backend. |
| `packaging` | Apache-2.0 OR BSD-2-Clause | Transitive dependency of `hatchling`. |
| `pathspec` | MPL-2.0 | Transitive dependency of `hatchling`. |
| `pluggy` | MIT | Transitive dependency of `hatchling`. |
| `trove-classifiers` | Apache-2.0 | Transitive dependency of `hatchling`. |

## Development and Test Dependencies

These packages are used for local development, CI, testing, type checking, and
package validation. They are not required for normal SDK use.

| Package | License | Notes |
| --- | --- | --- |
| `build` | MIT | Package build command. |
| `coverage` | Apache-2.0 | Test coverage reporting. |
| `mypy` | MIT | Static type checking. |
| `pyright` | MIT | Static type checking. |
| `pytest` | MIT | Test runner. |
| `pytest-asyncio` | Apache-2.0 | Async pytest support. |
| `respx` | BSD-3-Clause | HTTPX test mocking. |
| `ruff` | MIT | Formatting and linting. |
| `twine` | Apache-2.0 | Package distribution validation and upload tooling. |

## License Policy Summary

The SDK runtime dependency set is intentionally small and uses permissive
licenses, with the exception of MPL-2.0 packages (`certifi`, and `pathspec` for
build tooling). MPL-2.0 is a weak-copyleft license and is commonly accepted for
Python package usage, but it is not equivalent to Apache-2.0.

