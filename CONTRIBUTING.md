# Contributing

`zenture-sdk` is the public Python SDK for the zenture Public API. The current
repository contains the runtime SDK, typed contract layer, public docs,
examples, and packaging configuration used for prerelease validation.

## Development Standards

- Keep public APIs typed and exposed through `Zenture`, `AsyncZenture`, and
  resource attributes such as `client.chat`.
- Keep `_transport`, `_resources`, and `_contract` as implementation
  namespaces.
- Use Pydantic models for request, response, and configuration validation.
- Use `httpx` for sync and async HTTP transport.
- Do not log secrets, prompts, raw request bodies, or raw response bodies.
- Add deterministic tests for behavior changes.
- Keep README, docs, examples, and `AGENTS.md` aligned when public behavior
  changes.
- Maintainers may run controlled non-production checks by setting
  `ZENTURE_API_KEY` to a test token and `ZENTURE_BASE_URL` to an approved
  non-production API origin from the private environment runbook. Do not commit
  non-production hostnames, local port conventions, tokens, payloads, or logs.

## Pull Requests

Pull requests should include:

- a concise description of the change
- tests or a clear reason tests are not applicable
- documentation updates when behavior, public API, security posture, examples,
  or release process changes
- confirmation that no real zenture API tokens or customer data were added

## Local Checks

Run the full local gate before handing off SDK changes:

```bash
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy
python3 -m pyright
python3 -m pytest
python3 -m coverage run -m pytest
python3 -m coverage report
python3 -m build
python3 -m twine check dist/*
```

Tests must not hit the real zenture API. Use `httpx.MockTransport` or static
checks for docs and examples.

## Release Process

Public PyPI releases are blocked until the SDK reviewer gate passes. Publishing
must use PyPI Trusted Publishing through GitHub Actions OIDC, not long-lived
package tokens.
