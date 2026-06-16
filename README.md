# zenture-sdk

Official server-side only Python SDK for the zenture Public API.

`zenture-sdk` is for backend services, automation jobs, evaluation pipelines,
CI tasks, and controlled notebook environments. zenture API tokens are
server-side credentials. Do not put them in browsers, mobile apps, frontend
bundles, public notebooks, logs, analytics, traces, or customer-visible errors.

## Package Names

- Distribution: `zenture-sdk`
- Import package: `zenture`
- Sync client: `Zenture`
- Async client: `AsyncZenture`
- Supported Python: Python 3.11, 3.12, and 3.13

## Installation

```bash
pip install zenture-sdk
```

Until the public beta is published to PyPI, use the internally shared wheel or
release artifact from the repository owner.

## Authentication

Create API tokens in the existing zenture webapp with an existing account:
`https://ai.zenture.app/profile?tab=api-tokens`. The SDK does not provide an
API-token management surface.

Keep the token outside Python source code:

```bash
# .env, not committed
ZENTURE_API_KEY=your_webapp_created_api_token
```

```bash
set -a
. ./.env
set +a
```

The SDK intentionally does not parse `.env` files. Load environment variables
through your runtime, deployment platform, secrets manager, or preferred local
loader.

For controlled debugging only, `Zenture.from_env()` and
`AsyncZenture.from_env()` also read `ZENTURE_BASE_URL`. Valid remote origins
are `https://api.zenture.app` and `https://api-int.zenture.app`; local
`localhost`, `127.0.0.1`, and `[::1]` origins are accepted for local debugging.
Never derive `ZENTURE_BASE_URL` or constructor `base_url` values from user
input.

## API Documentation

The public API documentation lives at
`https://www.zenture.app/api-documentation`. Treat the committed OpenAPI
artifact in this repository as the SDK's local contract source of truth and use
the public documentation as the human-facing API reference.

## Sync Quickstart

```python
from zenture import Zenture

with Zenture.from_env() as client:
    print(client.helloworld())

    models = client.models.list(mode="single")
    for model in models.models:
        print(model.id, model.display_name)
```

## Async Quickstart

```python
import asyncio

from zenture import AsyncZenture


async def main() -> None:
    async with AsyncZenture.from_env() as client:
        result = await client.chat.run(
            message="Summarize this support note.",
            mode="single",
            idempotency_key="case-123-chat-single-v1",
            timeout=120.0,
        )
        print(result.status)


if __name__ == "__main__":
    asyncio.run(main())
```

## Models

```python
from zenture import Zenture

with Zenture.from_env() as client:
    single_models = client.models.list(mode="single")
    multi_models = client.models.list(mode="multi")
    print(single_models.models[0].id)
    print(multi_models.models[0].id)
```

## Chat

Single-model chat:

```python
from zenture import Zenture

with Zenture.from_env() as client:
    available_models = [
        model.id
        for model in client.models.list(mode="single").models
        if model.is_available
    ]
    if not available_models:
        raise RuntimeError("No available single-mode model for this token.")

    result = client.chat.run(
        message="Summarize this customer update.",
        mode="single",
        model=available_models[0],
        idempotency_key="case-123-chat-single-v1",
        timeout=120.0,
    )
    print(result.operation_id, result.status)
```

Multi-model chat:

```python
from zenture import Zenture

with Zenture.from_env() as client:
    available_models = [
        model.id
        for model in client.models.list(mode="multi").models
        if model.is_available
    ]
    if len(available_models) < 2:
        raise RuntimeError("At least two available multi-mode models are required.")

    result = client.chat.run(
        message="Compare these draft answers for factual consistency.",
        mode="multi",
        models=available_models[:2],
        idempotency_key="case-123-chat-multi-v1",
        timeout=120.0,
    )
    print(result.status)
```

Agentic chat mode is not part of Public V1. Do not document or add public
helpers for it in this SDK.

## Input Wizard

```python
from zenture import Zenture

with Zenture.from_env() as client:
    result = client.input_wizard.run(
        prompt="Improve this onboarding prompt for a support assistant.",
        idempotency_key="case-123-input-wizard-v1",
        timeout=120.0,
    )
    print(result.operation_id, result.status)
```

## Evaluations

```python
from zenture import Zenture

with Zenture.from_env() as client:
    result = client.evaluations.run(
        user_message="What is zenture?",
        ai_answer="zenture evaluates AI outputs.",
        idempotency_key="case-123-evaluation-v1",
        timeout=120.0,
    )
    print(result.operation_id, result.status)
```

## Operation Polling

Low-level create methods return an operation immediately. Use
`client.operations.wait(...)` when you want to poll explicitly.

```python
from zenture import Zenture

with Zenture.from_env() as client:
    operation = client.chat.create_operation(
        message="Review this response.",
        mode="single",
        idempotency_key="case-123-chat-create-v1",
    )
    final_operation = client.operations.wait(operation.operation_id, timeout=120.0)
    print(final_operation.status)
```

Terminal statuses are `succeeded`, `failed`, `cancelled`, and `expired`.

If `.run(...)` creates an operation and local polling later times out or is
stopped, the exception exposes `operation_id` and `idempotency_key` attributes.
Use `client.operations.get(exc.operation_id)` or retry with the same
`exc.idempotency_key`. Do not retry a billable mutation with a new key.

## Pagination

List-style read helpers support `limit` and `cursor`. The default page size is
`limit=50`, the maximum is `100`, and cursors are opaque strings. Responses
include `next_cursor`; `None` means there is no further page.

```python
from zenture import Zenture

with Zenture.from_env() as client:
    page = client.chat.list(limit=50)
    print(page.next_cursor)

    for chat in client.chat.iter(limit=50):
        print(chat.chat_id)
```

Available iterators:

- `client.chat.iter(limit=50, cursor=None)`
- `client.chat.iter_messages(chat_id, limit=50, cursor=None)`
- `client.evaluations.iter(limit=50, cursor=None)`

## Idempotency

Mutating routes require `Idempotency-Key`. Use stable caller-owned keys that do
not contain prompts, answers, API tokens, customer PII, or request bodies.

```python
from zenture import Zenture
from zenture.idempotency import idempotency_key

with Zenture.from_env() as client:
    key = idempotency_key("case-123", "chat", "v1")
    result = client.chat.run(
        message="Create a concise summary.",
        idempotency_key=key,
        timeout=120.0,
    )
    print(result.idempotency_key)
```

## Errors

```python
from zenture import Zenture
from zenture.errors import (
    ZentureAPIError,
    ZenturePollingTimeoutError,
    ZentureRateLimitError,
)

with Zenture.from_env() as client:
    try:
        result = client.chat.run(
            message="Summarize this incident.",
            idempotency_key="case-123-error-example-v1",
            timeout=120.0,
        )
        print(result.status)
    except ZenturePollingTimeoutError as exc:
        print(exc.operation_id)
    except ZentureRateLimitError as exc:
        print(exc.retry_after)
    except ZentureAPIError as exc:
        print(exc.request_id)
```

SDK exceptions redact sensitive content. Request and response bodies are not
included in exception strings.

## Timeout, Retry, Polling, and Rate Limits

- SDK-owned HTTP clients use explicit timeouts: connect `5s`,
  read/write/pool `30s`.
- `operations.wait(timeout=...)` and `.run(timeout=...)` use a total operation
  polling budget, not the raw HTTP read timeout.
- Polling uses deterministic intervals: `initial_interval=1s`, doubled up to
  `max_interval=8s`, with no jitter.
- Retry default is `max_retries=2`.
- Retryable HTTP responses include `429`, `500`, `502`, `503`, and `504` when
  the public error code is retryable.
- `Retry-After` is honored before deterministic exponential backoff.
- Mutating requests are retried only when an `Idempotency-Key` is present.

## Base URL Policy

- Default production API origin: `https://api.zenture.app`
- INT origin for controlled debugging: `https://api-int.zenture.app`
- Local `localhost`, `127.0.0.1`, and `[::1]` origins are only for local
  debugging.
- `ZENTURE_BASE_URL` is supported by `from_env()` for controlled debugging.
- Never derive `base_url` from user input.
- URL credentials, paths, query strings, fragments, and arbitrary HTTPS origins
  are rejected.

## Public V1 Scope

- No browser, mobile, or frontend bundle usage.
- No API-token management surface.
- No public helper for agentic chat mode in Public V1.
- No top-level exports from internal `_contract` modules.

## Local Verification

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

## Security

See [`SECURITY.md`](./SECURITY.md) for vulnerability reporting and security
expectations. Do not publish API tokens in issues, logs, screenshots, or support
requests.

## License

Apache License 2.0. See [`LICENSE`](./LICENSE).
