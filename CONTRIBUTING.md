# Contributing

`zenture-sdk` is being prepared as a public Python SDK for the zenture Public API.
The repository is currently in planning/bootstrap state. Runtime SDK implementation
starts only after the Public API OpenAPI contract is finalized for SDK beta.

## Development Standards

- Keep public APIs typed.
- Use Pydantic models for public request and response data.
- Use `httpx` for sync and async HTTP transport.
- Do not log secrets, prompts, raw request bodies, or raw response bodies.
- Keep generated OpenAPI code isolated under `zenture._generated`.
- Keep hand-written modules small and reviewable.
- Add deterministic tests for behavior changes.

## Pull Requests

Pull requests should include:

- a concise description of the change
- tests or a clear reason tests are not applicable
- documentation updates when behavior, public API, security posture, or release
  process changes
- confirmation that no real zenture API tokens or customer data were added

## Local Checks

The full SDK toolchain will be added during repository foundation. Until then,
the bootstrap CI validates required governance files and repository hygiene.

Expected final checks before SDK beta:

- Ruff format and lint
- Mypy strict
- Pyright
- Pytest with coverage
- mocked HTTP integration tests
- example execution against fixtures
- OpenAPI contract drift checks

## Release Process

Public PyPI releases are blocked until the SDK reviewer gate passes. Publishing
must use PyPI Trusted Publishing through OIDC, not long-lived package tokens.
