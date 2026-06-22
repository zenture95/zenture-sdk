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

first_turn_key = idempotency_key("case-123", "chat-turn-1", "v1")
follow_up_key = idempotency_key("case-123", "chat-turn-2", "v1")
external_eval_key = idempotency_key("support-ticket-123-answer-a", "evaluate", "v1")
chat_answer_eval_key = idempotency_key("response_abc123", "evaluate", "v1")
```

Do not put prompts, answers, API tokens, customer PII, raw request bodies, or
secret material in idempotency keys. Keep keys short, stable, and meaningful for
support and replay correlation.

`external_id` is separate from `idempotency_key`. For external evaluations,
`external_id` is optional caller-side correlation stored with the evaluation;
`idempotency_key` is the required retry-safety key for the mutation.

## Common Patterns

Chat turn keys should be stable per turn:

```python
client.chat.run(
    message="Summarize this support note.",
    idempotency_key=idempotency_key("case-123", "chat-turn-1", "v1"),
)

client.chat.run(
    message="Turn it into next steps.",
    chat_id="chat_example",
    idempotency_key=idempotency_key("case-123", "chat-turn-2", "v1"),
)
```

External evaluation keys should identify the external answer, not include the
answer text:

```python
client.evaluations.run(
    user_message="...",
    ai_answer="...",
    external_id="support-ticket-123-answer-a",
    idempotency_key=idempotency_key("support-ticket-123-answer-a", "evaluate", "v1"),
)
```

Internal chat-answer evaluation keys can use the safe zenture
`model_response_id`:

```python
client.evaluations.run(
    user_message=turn.user_message,
    ai_answer=turn.model_answer,
    chat_id=chat_id,
    turn_id=turn.turn_id,
    model_response_id=turn.model_response_id,
    idempotency_key=idempotency_key(turn.model_response_id, "evaluate", "v1"),
)
```

## Retry Safety

If a `.run(...)` helper creates an operation and local polling later times out
or is stopped, catch the polling exception and reuse `exc.idempotency_key`.
Alternatively call `client.operations.get(exc.operation_id)` to resume from the
operation reference. Do not retry the same billable mutation with a new key.
