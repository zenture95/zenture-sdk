# Security Policy

## Supported Versions

`zenture-sdk` is not public-release stable yet. Security reports are still welcome
for prerelease code, documentation, examples, packaging, CI, and release workflows.

## Reporting a Vulnerability

Report suspected vulnerabilities privately through GitHub Security Advisories on
the `zenture-sdk` repository once the public repository is enabled. If GitHub
Security Advisories are not available, contact the zenture maintainers through
the private security contact listed in the organization profile.

Do not disclose vulnerabilities publicly until zenture has acknowledged the report
and coordinated a fix or mitigation.

## Secret Handling Expectations

zenture API tokens are server-side credentials. They must not be embedded in
browsers, mobile apps, frontend bundles, public repositories, notebooks with
shared output, logs, analytics, traces, or customer-visible error reports.

The SDK must not log or expose:

- API tokens or Authorization headers
- JWTs
- prompts or model answers
- raw request or response bodies
- payment, billing, or provider payloads

Examples and tests must use fake credentials only.

## Release Security

Public package publishing must use PyPI Trusted Publishing through GitHub Actions
OIDC. Long-lived PyPI API tokens are not allowed in repository secrets.

Before any public PyPI release, the repository must have:

- branch protection or rulesets on the default branch
- required CI checks
- CODEOWNERS review for protected paths
- secret scanning and push protection
- dependency update automation
- protected `pypi` release environment with manual approval
