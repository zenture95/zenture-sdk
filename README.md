# zenture-sdk

Official Python SDK for the zenture Public API.

This repository is currently in governance and SDK-planning bootstrap. Runtime SDK
implementation starts after the zenture Public API OpenAPI contract is finalized
for SDK beta.

## Planned Package Names

- PyPI distribution: `zenture-sdk`
- Python import package: `zenture`
- Sync client: `Zenture`
- Async client: `AsyncZenture`

## Security Notice

zenture API tokens are server-side credentials. Do not embed them in browsers,
mobile apps, frontend bundles, public repositories, logs, analytics, traces, or
customer-visible error reports.

The SDK will never require API token creation from code in V1. API tokens are
created and managed through the existing zenture webapp account flow.

## Current Status

The implementation plan is maintained in the private repository during SDK
bootstrap. It is intentionally not shipped in package artifacts.

Before public prerelease, this repository must have:

- branch protection or GitHub rulesets
- required CI checks
- CODEOWNERS review for protected paths
- secret scanning and push protection
- dependency update automation
- PyPI Trusted Publishing through GitHub Actions OIDC

## License

Apache License 2.0. See [`LICENSE`](./LICENSE).
