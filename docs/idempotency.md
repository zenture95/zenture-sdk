# Idempotency

Mutating public API routes require an `Idempotency-Key`. This protects callers
from duplicate billable work when a request is retried after a timeout, rate
limit, process restart, or network interruption.

Low-level create methods require a caller-provided key. High-level `.run(...)`
helpers may generate a key when one is omitted, but they expose the generated
key in the result or in local polling exceptions.

## Key Design

Use stable caller-owned identifiers:

```python
from zenture.idempotency import idempotency_key

key = idempotency_key("case-123", "chat", "v1")
```

Do not put prompts, answers, API tokens, customer PII, raw request bodies, or
secret material in idempotency keys. Keep keys short, stable, and meaningful for
support and replay correlation.

## Retry Safety

If a `.run(...)` helper creates an operation and local polling later times out
or is stopped, catch the polling exception and reuse `exc.idempotency_key`.
Alternatively call `client.operations.get(exc.operation_id)` to resume from the
operation reference. Do not retry the same billable mutation with a new key.
