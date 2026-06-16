# API Reference Overview

This is a compact public overview, not a generated reference.

The human-facing public API documentation lives at
`https://www.zenture.app/api-documentation`. This SDK also ships the local
OpenAPI contract artifact under `openapi/zenture-public-api-v1.openapi.json` for
deterministic contract-drift tests.

## Clients

- `Zenture`: synchronous client using `httpx.Client`.
- `AsyncZenture`: asynchronous client using `httpx.AsyncClient`.

Both clients support `from_env()`, explicit close methods, and context manager
usage.

## Resources

- `client.helloworld()`: quick connectivity check.
- `client.models.list(mode=None | "single" | "multi")`: discover public model
  identifiers available to the current token.
- `client.chat.create(...)`: create a chat operation. This is an alias for
  `client.chat.create_operation(...)`.
- `client.chat.create_operation(...)`: create a chat operation and return the
  initial operation response.
- `client.chat.run(...)`: create and wait for chat.
- `client.chat.list(limit=50, cursor=None)`: list public chat summaries
  available to the token.
- `client.chat.iter(limit=50, cursor=None)`: iterate public chat summaries until
  `next_cursor` is `None`.
- `client.chat.get(chat_id)`: fetch one public chat summary.
- `client.chat.messages(chat_id, limit=50, cursor=None)`: fetch public chat
  turns for a chat.
- `client.chat.iter_messages(chat_id, limit=50, cursor=None)`: iterate public
  chat turns until `next_cursor` is `None`.
- `client.input_wizard.create(...)`: create an input wizard operation.
- `client.input_wizard.run(...)`: create and wait for input wizard.
- `client.evaluations.create(...)`: create an evaluation operation.
- `client.evaluations.run(...)`: create and wait for evaluation.
- `client.evaluations.list(limit=50, cursor=None)`: list public evaluations
  available to the token.
- `client.evaluations.iter(limit=50, cursor=None)`: iterate public evaluations
  until `next_cursor` is `None`.
- `client.evaluations.get(evaluation_id)`: fetch one public evaluation.
- `client.operations.get(operation_id)`: fetch one operation.
- `client.operations.wait(operation_id, ...)`: poll until terminal.
- `client.billing.get()`: fetch public billing status.
- `client.usage.get(scope="api")`: fetch API-token usage counters.
- `client.usage.get(scope="all")`: fetch all usage counters visible to the
  token.
- `client.limits.get()`: fetch public route and operation limits.

Paginated read methods accept `limit` from `1` to `100` and optional opaque
`cursor` values up to `200` characters. The API sorts paginated collections by
`created_at desc`; `next_cursor is None` means there is no further page.
