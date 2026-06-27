# API Reference

This is the compact resource index for the zenture Python SDK. Use it as the
map of available clients, resources, and flows.

The human-facing public API documentation lives at
`https://www.zenture.app/developers`. This SDK also ships the local
OpenAPI contract artifact under `openapi/zenture-public-api-v1.openapi.json` for
deterministic contract-drift tests.

For copy-paste calls, HTTP routes, and example response structures for every
SDK/API call, use [`sdk-call-reference.md`](./sdk-call-reference.md).
For raw JSON response bodies and SDK model mapping, use
[`response-shapes.md`](./response-shapes.md).

## Clients

- `Zenture`: synchronous client using `httpx.Client`.
- `AsyncZenture`: asynchronous client using `httpx.AsyncClient`.

Both clients support `from_env()`, explicit close methods, and context manager
usage.

## Resource Index

### Connectivity

- `client.helloworld()`: quick connectivity check. See
  [`client.helloworld()`](./sdk-call-reference.md#clienthelloworld).

### Models

- `client.models.list(mode=None | "single" | "multi")`: discover public model
  identifiers available to the current token. See
  [`client.models.list(...)`](./sdk-call-reference.md#clientmodelslist).

### Chat

- `client.chat.create(...)`: create a chat operation. This is an alias for
  `client.chat.create_operation(...)`. See
  [`client.chat.create(...)`](./sdk-call-reference.md#clientchatcreate).
- `client.chat.create_operation(...)`: create a chat operation and return the
  initial operation response. See
  [`client.chat.create_operation(...)`](./sdk-call-reference.md#clientchatcreate_operation).
- `client.chat.run(...)`: create and wait for chat. See
  [`client.chat.run(...)`](./sdk-call-reference.md#clientchatrun).
- `client.chat.list(limit=50, cursor=None)`: list public chat summaries
  available to the token. See
  [`client.chat.list(...)`](./sdk-call-reference.md#clientchatlist).
- `client.chat.iter(limit=50, cursor=None)`: iterate public chat summaries until
  `next_cursor` is `None`. See
  [`client.chat.iter(...)`](./sdk-call-reference.md#clientchatiter).
- `client.chat.get(chat_id)`: fetch one public chat summary. See
  [`client.chat.get(...)`](./sdk-call-reference.md#clientchatget).
- `client.chat.messages(chat_id, limit=50, cursor=None)`: fetch public chat
  turns for a chat. See
  [`client.chat.messages(...)`](./sdk-call-reference.md#clientchatmessages).
- `client.chat.iter_messages(chat_id, limit=50, cursor=None)`: iterate public
  chat turns until `next_cursor` is `None`. See
  [`client.chat.iter_messages(...)`](./sdk-call-reference.md#clientchatiter_messages).

### Input Wizard

- `client.input_wizard.create(...)`: create an input wizard operation. See
  [`client.input_wizard.create(...)`](./sdk-call-reference.md#clientinput_wizardcreate).
- `client.input_wizard.run(...)`: create and wait for input wizard. See
  [`client.input_wizard.run(...)`](./sdk-call-reference.md#clientinput_wizardrun).

### Evaluations

- `client.evaluations.create(...)`: create an evaluation operation. See
  [`client.evaluations.create(...)`](./sdk-call-reference.md#clientevaluationscreate).
- `client.evaluations.run(...)`: create and wait for evaluation. See external
  [`client.evaluations.run(...)`](./sdk-call-reference.md#clientevaluationsrun-for-external-answers)
  and internal
  [`client.evaluations.run(...)`](./sdk-call-reference.md#clientevaluationsrun-for-internal-zenture-chat-answers)
  examples.
- `client.evaluations.list(limit=50, cursor=None)`: list public evaluations
  available to the token. See
  [`client.evaluations.list(...)`](./sdk-call-reference.md#clientevaluationslist).
- `client.evaluations.iter(limit=50, cursor=None)`: iterate public evaluations
  until `next_cursor` is `None`. See
  [`client.evaluations.iter(...)`](./sdk-call-reference.md#clientevaluationsiter).
- `client.evaluations.get(evaluation_id)`: fetch one public evaluation. See
  [`client.evaluations.get(...)`](./sdk-call-reference.md#clientevaluationsget).

### Operations

- `client.operations.get(operation_id)`: fetch one operation. See
  [`client.operations.get(...)`](./sdk-call-reference.md#clientoperationsget).
- `client.operations.wait(operation_id, ...)`: poll until terminal. See
  [`client.operations.wait(...)`](./sdk-call-reference.md#clientoperationswait).

### Account Reads

- `client.wallet.get()`: fetch public wallet plan and available credits. See
  [`client.wallet.get()`](./sdk-call-reference.md#clientwalletget).
- `client.usage.get(scope="api")`: fetch API-token usage counters. See
  [`client.usage.get(...)`](./sdk-call-reference.md#clientusageget).
- `client.usage.get(scope="all")`: fetch all usage counters visible to the
  token. See [`client.usage.get(...)`](./sdk-call-reference.md#clientusageget).
- `client.limits.get()`: fetch public route and operation limits. See
  [`client.limits.get()`](./sdk-call-reference.md#clientlimitsget).

See [`account-reads.md`](./account-reads.md) for wallet, usage, and limits
examples.

For a complete prompt-improvement, chat, evaluation, and cost-summary flow, see
[`examples/end_to_end_chat_evaluation.py`](../examples/end_to_end_chat_evaluation.py).

Paginated read methods accept `limit` from `1` to `100` and optional opaque
`cursor` values up to `200` characters. The API sorts paginated collections by
`created_at desc`; `next_cursor is None` means there is no further page.

Evaluation creation requires `user_message` and `ai_answer`. New external
evaluations may include `external_id` and bounded `metadata` for caller-side
correlation. `model_response_id` keeps the legacy zenture chat-backed target
path; `chat_id` and `turn_id` are correlation-only unless a legacy
`model_response_id` is supplied.

## Evaluation Flows

Use `model_response_id` when the answer came from zenture chat history. This is
the AI-answer id, not the user-message id. The evaluation still sends the
`user_message` and `ai_answer` text, and `model_response_id` binds the request to
the existing owned zenture response.

```python
from zenture import Zenture
from zenture.idempotency import idempotency_key

with Zenture.from_env() as client:
    first = client.chat.run(
        message="Give me a concise onboarding checklist for a new API user.",
        mode="single",
        idempotency_key=idempotency_key("case-42", "chat-first", "v1"),
    )
    chat_id = first.result.chat_id

    follow_up = client.chat.run(
        message="Turn that checklist into three short implementation steps.",
        chat_id=chat_id,
        mode="single",
        idempotency_key=idempotency_key("case-42", "chat-follow-up", "v1"),
    )

    turn_id = follow_up.result.turn_id
    model_response_id = (
        follow_up.result.model_response_id
        or follow_up.result.model_response_ids[0]
    )

    turn = next(
        item for item in client.chat.messages(chat_id).turns
        if item.turn_id == turn_id
    )

    evaluation = client.evaluations.run(
        user_message=turn.user_message,
        ai_answer=turn.model_answer,
        chat_id=chat_id,
        turn_id=turn_id,
        model_response_id=model_response_id,
        idempotency_key=idempotency_key("case-42", "evaluate-chat-answer", "v1"),
    )
```

Use the external path when the answer came from your own application or another
AI system. Do not send `chat_id`, `turn_id`, or `model_response_id`; the
evaluation is stored as an external evaluation-only record and is not added to
zenture chat history.

For external answers with sources, put the sources directly into `ai_answer` as
Markdown links, footnotes, or plain URLs. Public V1 does not require a separate
structured `sources` field; zenture evaluates the Markdown answer as submitted.

Billing and evaluation result fields:

- Completed chat and evaluation operations include `amount_billed` when the
  ledger debit is available, for example `{"amount": "4.41", "unit": "credits"}`.
- `amount_billed.amount` is the display credit amount with two decimal places,
  not an internal subunit field.
- `client.evaluations.get(evaluation_id)` returns `zenture_summary`,
  `zenture_suggestion`, `zenture_kpi_details`, `results`, and `sources` when
  the evaluation has completed.
- `sources` is grouped by model. Source rows can include `status` or
  `retrievalStatus` (`available`, `limited`, `unavailable`, `unverified`),
  `httpStatus`, `verdict`, `url`, `hostname`, `securityLabel`,
  `accessibilityScore`, and `responseTimeMs`.

```python
from zenture import Zenture
from zenture.idempotency import idempotency_key

with Zenture.from_env() as client:
    evaluation = client.evaluations.run(
        user_message="What does the SDK do?",
        ai_answer=(
            "It helps server-side Python integrations call zenture. "
            "[Source](https://example.com/sdk-brief)"
        ),
        external_id="support-ticket-123-answer-a",
        metadata={"source": "support_bot", "answer_format": "markdown_with_sources"},
        idempotency_key=idempotency_key("support-ticket-123", "evaluate", "v1"),
    )
```
