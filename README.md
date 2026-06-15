# zenture-sdk

Official Python SDK for the zenture Public API.

This repository is currently in private SDK bootstrap. The package foundation,
core runtime primitives and first public resource clients are implemented. The
repository is not ready for public PyPI beta until the reviewer gate is complete.

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

Implemented locally:

- modern Python package foundation with `src/zenture` and `py.typed`
- strict Pydantic-based SDK models and configuration
- secret redaction helpers
- typed SDK error model
- idempotency, polling and rate-limit primitives
- sync/async `httpx` transport lifecycle primitives with explicit timeout and
  retry policy
- OpenAPI artifact mirrored under `openapi/` and included in the source distribution
- internal `zenture._contract` models for operation responses, operation results,
  public errors, mutation requests, read responses and rate-limit headers
- public `Zenture` / `AsyncZenture` clients
- `helloworld` quickstart endpoint
- resource clients for operations, chat, input wizard, evaluations, billing,
  usage, limits and model discovery
- single- and multi-model chat request support
- chat operation `.run()` helper
- contract drift tests for `POST /v1/evaluate`, `missing_idempotency_key`,
  `GET /v1/models`, bounded `PublicOperationResult`, API-token management
  exclusion and operation status alignment

Not implemented yet:

- generic operation polling / `.run()` helpers for all async resources
- full generated client layer
- pagination helpers; current OpenAPI list routes expose `next_cursor` responses
  but no `limit` / `cursor` request parameters yet

## Quickstart

Set the API key outside Python source code. For local development you can keep
it in an uncommitted `.env` file and export it before starting Python:

```bash
# .env
ZENTURE_API_KEY=your_webapp_created_api_token
```

```bash
set -a
. ./.env
set +a
```

```python
from zenture import Zenture

client = Zenture.from_env()

print(client.helloworld())

models = client.models.list(mode="single")
for model in models.models:
    print(model.id, model.display_name)

operation = client.chat.create_operation(
    message="Evaluate this answer after it completes.",
    mode="single",
    model=None,
    idempotency_key="customer-123-chat-001",
)
print(operation.operation_id)

multi_model_result = client.chat.run(
    message="Compare these model responses for factual consistency.",
    mode="multi",
    models=["public-model-a", "public-model-b"],
    idempotency_key="customer-123-chat-multi-001",
    timeout=120.0,
)
print(multi_model_result.status)

evaluation = client.evaluations.create(
    user_message="What is zenture?",
    ai_answer="zenture evaluates AI outputs.",
    idempotency_key="customer-123-eval-001",
)
print(evaluation.status)

client.close()
```

The SDK intentionally does not parse `.env` files itself. Load secrets into the
process environment through your runtime, deployment platform, secrets manager
or preferred local `.env` loader.

Model selection policy:

- `client.models.list(mode="single")` and `client.models.list(mode="multi")`
  discover public model identifiers available to the current API token.
- Chat defaults to `mode="single"` and accepts at most one `model`.
- `mode="multi"` requires `models` with 1 to 3 unique public model IDs.
- Agentic chat is not public in V1 and has no SDK helper.
- Server-side plan, billing, permission and availability checks remain the
  authority.

Base URL policy:

- default production API origin is `https://api.zenture.app`
- overrides are allowed only for `https://api-int.zenture.app` and local
  debugging origins on `localhost`, `127.0.0.1` or `::1`
- URL credentials, paths, query strings, fragments and arbitrary HTTPS origins
  are rejected
- never derive `base_url` from user input

Transport policy:

- SDK-owned HTTP clients use explicit timeouts: connect `5s`, read/write/pool
  `30s`.
- Retry default is `max_retries=2`.
- Retryable HTTP responses include `429`, `500`, `502`, `503` and `504` when
  the public error code is retryable.
- Mutating requests are retried only when an `Idempotency-Key` is present.
- `Retry-After` is honored before deterministic exponential backoff, capped at
  `8s`.
- `chat.run(timeout=...)` is the operation polling budget, not the raw HTTP
  read timeout.

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
