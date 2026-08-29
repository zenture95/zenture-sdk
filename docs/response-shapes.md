<!-- Generated from OpenAPI. Do not edit manually. -->
# Response Shapes

This page documents sanitized request examples and raw zenture Public API response bodies.
The committed OpenAPI artifact remains the contract source of truth; this file is generated from that artifact for SDK documentation and reviewable downstream diffs.

## Conventions

- Timestamps are ISO-8601 strings with timezone information.
- `null` means the field is optional, unavailable, or intentionally absent.
- Credit amounts use display strings such as `{"amount": "123.45", "unit": "credits"}`.
- Operation statuses are `queued`, `running`, `succeeded`, `failed`, `cancelled`, and `expired`.
- Mutating async routes return `PublicOperationResponse`; SDK `.run(...)` helpers wrap terminal operations in `OperationRunResult`.
- `PublicOperationError.code` is a domain operation code string and is separate from gateway error-envelope codes.
- Rate-limit data is returned as HTTP headers, not in response bodies.
- Agentic chat is not a Public V1 mode and has no public SDK helper.

## Endpoint Summary

| Method | Endpoint | Success | SDK surface | SDK model |
| --- | --- | --- | --- | --- |
| `POST` | `/v1/chat` | `202` | `client.chat.create(...)`, `client.chat.create_operation(...)`, `client.chat.run(...)` | `PublicOperationResponse`, `OperationRunResult` |
| `GET` | `/v1/chats` | `200` | `client.chat.list(...)`, `client.chat.iter(...)` | `PublicChatCollectionResponse` |
| `GET` | `/v1/chats/{chat_id}` | `200` | `client.chat.get(...)` | `PublicChatResponse` |
| `GET` | `/v1/chats/{chat_id}/messages` | `200` | `client.chat.messages(...)`, `client.chat.iter_messages(...)` | `PublicChatMessagesResponse` |
| `POST` | `/v1/evaluate` | `202` | `client.evaluations.create(...)`, `client.evaluations.run(...)` | `PublicOperationResponse`, `OperationRunResult` |
| `GET` | `/v1/evaluations` | `200` | `client.evaluations.list(...)`, `client.evaluations.iter(...)` | `PublicEvaluationCollectionResponse` |
| `GET` | `/v1/evaluations/{evaluation_id}` | `200` | `client.evaluations.get(...)` | `PublicEvaluationResponse` |
| `GET` | `/v1/helloworld` | `200` | `client.helloworld()` | `str` |
| `POST` | `/v1/input-wizard` | `202` | `client.input_wizard.create(...)`, `client.input_wizard.run(...)` | `PublicOperationResponse`, `OperationRunResult` |
| `GET` | `/v1/limits` | `200` | `client.limits.get()` | `LimitsResponse` |
| `GET` | `/v1/models` | `200` | `client.models.list(mode=None | "single" | "multi")` | `PublicModelListResponse` |
| `GET` | `/v1/operations/{operation_id}` | `200` | `client.operations.get(...)`, `client.operations.wait(...)` | `PublicOperationResponse` |
| `POST` | `/v1/runs` | `202` | `httpx` direct call | `PublicPhase1RunResponse` |
| `GET` | `/v1/runs/{run_id}` | `200` | `httpx` direct call | `PublicPhase1RunResponse` |
| `GET` | `/v1/usage` | `200` | `client.usage.get(...)` | `PublicUsageResponse` |
| `GET` | `/v1/wallet` | `200` | `client.wallet.get()` | `PublicWalletResponse` |

## Shared Objects

### `PublicAmountBilled`

```json
{
  "amount": "123.45",
  "unit": "credits"
}
```

### `PublicOperationResponse`

`PublicOperationResponse.result` is either `null` or a bounded `PublicOperationResult`.

```json
{
  "operation_id": "op_example",
  "status": "queued",
  "result": null,
  "error": null
}
```

Terminal success example:

```json
{
  "operation_id": "op_example",
  "status": "succeeded",
  "result": {
    "result_type": "chat",
    "chat_id": "chat_example",
    "turn_id": "turn_example",
    "model_response_id": "response_example",
    "model_response_ids": [
      "response_example"
    ],
    "status": "succeeded",
    "completed_at": "2026-06-15T10:00:30Z",
    "amount_billed": {
      "amount": "123.45",
      "unit": "credits"
    }
  },
  "error": null
}
```

Terminal failure example:

```json
{
  "operation_id": "op_example",
  "status": "failed",
  "result": null,
  "error": {
    "code": "chat_execution_failed",
    "message": "Chat execution failed."
  }
}
```

### `PublicOperationResult`

```json
{
  "result_type": "chat",
  "chat_id": "chat_example",
  "turn_id": "turn_example",
  "model_response_id": "response_example",
  "model_response_ids": [
    "response_example"
  ],
  "evaluation_id": null,
  "resource_id": "chat_example",
  "status": "succeeded",
  "completed_at": "2026-06-15T10:00:30Z",
  "amount_billed": {
    "amount": "123.45",
    "unit": "credits"
  },
  "score": null,
  "target_kind": null
}
```

### `OperationRunResult`

`OperationRunResult` is SDK-only and is not returned as raw HTTP JSON.

```json
{
  "operation_id": "op_example",
  "status": "succeeded",
  "result": {
    "result_type": "chat",
    "chat_id": "chat_example",
    "turn_id": "turn_example",
    "model_response_id": "response_example",
    "model_response_ids": [
      "response_example"
    ],
    "amount_billed": {
      "amount": "123.45",
      "unit": "credits"
    }
  },
  "error": null,
  "chat_turn": null,
  "evaluation": null,
  "idempotency_key": "caller-owned-idempotency-key",
  "last_request_id": null
}
```

## Endpoint Details

### `POST /v1/chat`

SDK surface: `client.chat.create(...)`, `client.chat.create_operation(...)`, `client.chat.run(...)`

SDK model: `PublicOperationResponse`, `OperationRunResult`

Auth mode: `api_token`

Scopes: `chat:write`

Idempotency: `required`

Request body schema: `ChatRequest`

Request body example:

```json
{
  "message": "Summarize this support update.",
  "mode": "single"
}
```

Response `202` as `application/json`:

Schema: `PublicOperationResponse`

```json
{
  "operation_id": "op_example",
  "status": "queued",
  "result": null,
  "error": null
}
```

### `GET /v1/chats`

SDK surface: `client.chat.list(...)`, `client.chat.iter(...)`

SDK model: `PublicChatCollectionResponse`

Auth mode: `api_token`

Scopes: `chat:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicChatCollectionResponse`

```json
{
  "chats": [
    {
      "chat_id": "chat_example",
      "created_at": null,
      "title": null,
      "updated_at": null
    }
  ],
  "next_cursor": null
}
```

### `GET /v1/chats/{chat_id}`

SDK surface: `client.chat.get(...)`

SDK model: `PublicChatResponse`

Auth mode: `api_token`

Scopes: `chat:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicChatResponse`

```json
{
  "chat": {
    "chat_id": "chat_example",
    "created_at": null,
    "title": null,
    "updated_at": null
  },
  "latest_turns": [
    {
      "created_at": null,
      "model_answer": "example",
      "model_response_id": null,
      "model_response_ids": [
        "example"
      ],
      "turn_id": "turn_example",
      "user_message": "How should we respond?"
    }
  ]
}
```

### `GET /v1/chats/{chat_id}/messages`

SDK surface: `client.chat.messages(...)`, `client.chat.iter_messages(...)`

SDK model: `PublicChatMessagesResponse`

Auth mode: `api_token`

Scopes: `chat:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicChatMessagesResponse`

```json
{
  "chat_id": "chat_example",
  "next_cursor": null,
  "turns": [
    {
      "created_at": null,
      "model_answer": "example",
      "model_response_id": null,
      "model_response_ids": [
        "example"
      ],
      "turn_id": "turn_example",
      "user_message": "How should we respond?"
    }
  ]
}
```

### `POST /v1/evaluate`

SDK surface: `client.evaluations.create(...)`, `client.evaluations.run(...)`

SDK model: `PublicOperationResponse`, `OperationRunResult`

Auth mode: `api_token`

Scopes: `evaluation:run`

Idempotency: `required`

Request body schema: `EvaluateRequest`

Request body example:

```json
{
  "user_message": "How should we respond?",
  "ai_answer": "Offer a concise next step.",
  "external_id": "case-123"
}
```

Response `202` as `application/json`:

Schema: `PublicOperationResponse`

```json
{
  "operation_id": "op_example",
  "status": "queued",
  "result": null,
  "error": null
}
```

### `GET /v1/evaluations`

SDK surface: `client.evaluations.list(...)`, `client.evaluations.iter(...)`

SDK model: `PublicEvaluationCollectionResponse`

Auth mode: `api_token`

Scopes: `evaluation:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicEvaluationCollectionResponse`

```json
{
  "evaluations": [
    {
      "amount_billed": "example",
      "created_at": null,
      "evaluation_id": "eval_example",
      "results": null,
      "score": null,
      "sources": null,
      "status": "active",
      "zenture_kpi_details": null,
      "zenture_suggestion": null,
      "zenture_summary": null
    }
  ],
  "next_cursor": null
}
```

### `GET /v1/evaluations/{evaluation_id}`

SDK surface: `client.evaluations.get(...)`

SDK model: `PublicEvaluationResponse`

Auth mode: `api_token`

Scopes: `evaluation:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicEvaluationResponse`

```json
{
  "amount_billed": {
    "amount": "123.45",
    "unit": "credits"
  },
  "created_at": null,
  "evaluation_id": "eval_example",
  "results": null,
  "score": null,
  "sources": null,
  "status": "active",
  "zenture_kpi_details": null,
  "zenture_suggestion": null,
  "zenture_summary": null
}
```

### `GET /v1/helloworld`

SDK surface: `client.helloworld()`

SDK model: `str`

Auth mode: `none`

Scopes: `none`

Idempotency: `not required`

Request body: none

Response `200` as `text/markdown`:

Schema: `string`

```markdown
# zenture Public API

Base URL: `https://api.zenture.app/v1`

Developer docs: `https://www.zenture.app/developers`

Python SDK: [zenture95/zenture-sdk](https://github.com/zenture95/zenture-sdk)
```

### `POST /v1/input-wizard`

SDK surface: `client.input_wizard.create(...)`, `client.input_wizard.run(...)`

SDK model: `PublicOperationResponse`, `OperationRunResult`

Auth mode: `api_token`

Scopes: `input_wizard:run`

Idempotency: `required`

Request body schema: `InputWizardRequest`

Request body example:

```json
{
  "mode": "prompt_improvement",
  "prompt": "Draft a customer-facing answer from these notes."
}
```

Response `202` as `application/json`:

Schema: `PublicOperationResponse`

```json
{
  "operation_id": "op_example",
  "status": "queued",
  "result": null,
  "error": null
}
```

### `GET /v1/limits`

SDK surface: `client.limits.get()`

SDK model: `LimitsResponse`

Auth mode: `api_token`

Scopes: `rate_limits:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `LimitsResponse`

```json
{
  "operation_statuses": [
    "example"
  ],
  "routes": {}
}
```

### `GET /v1/models`

SDK surface: `client.models.list(mode=None | "single" | "multi")`

SDK model: `PublicModelListResponse`

Auth mode: `api_token`

Scopes: `models:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicModelListResponse`

```json
{
  "models": [
    {
      "id": "model_public_single",
      "display_name": "Public Single",
      "modes": [
        "single"
      ],
      "capabilities": [
        "chat"
      ],
      "is_default": true,
      "is_available": true,
      "cost_class": "standard",
      "provider_display_name": "Example Provider",
      "max_input_tokens": 8192
    }
  ]
}
```

### `GET /v1/operations/{operation_id}`

SDK surface: `client.operations.get(...)`, `client.operations.wait(...)`

SDK model: `PublicOperationResponse`

Auth mode: `api_token`

Scopes: `none`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicOperationResponse`

```json
{
  "operation_id": "op_example",
  "status": "succeeded",
  "result": null,
  "error": null
}
```

### `POST /v1/runs`

SDK surface: `httpx` direct call

SDK model: `PublicPhase1RunResponse`

Auth mode: `api_token`

Scopes: `evaluation:run`

Idempotency: `required`

Request body schema: `Phase1RunRequest`

Request body example:

```json
{
  "profile": "fast"
}
```

Response `202` as `application/json`:

Schema: `PublicPhase1RunResponse`

```json
{
  "disposition": "accepted",
  "generation": null,
  "jobs_ahead": null,
  "public_run_id": "example",
  "queue_reason": null,
  "queued_at": null,
  "status": "active"
}
```

### `GET /v1/runs/{run_id}`

SDK surface: `httpx` direct call

SDK model: `PublicPhase1RunResponse`

Auth mode: `api_token`

Scopes: `evaluation:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicPhase1RunResponse`

```json
{
  "disposition": "accepted",
  "generation": null,
  "jobs_ahead": null,
  "public_run_id": "example",
  "queue_reason": null,
  "queued_at": null,
  "status": "active"
}
```

### `GET /v1/usage`

SDK surface: `client.usage.get(...)`

SDK model: `PublicUsageResponse`

Auth mode: `api_token`

Scopes: `usage:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicUsageResponse`

```json
{
  "operation_count": 1,
  "scope": "api"
}
```

### `GET /v1/wallet`

SDK surface: `client.wallet.get()`

SDK model: `PublicWalletResponse`

Auth mode: `api_token`

Scopes: `wallet:read`

Idempotency: `not required`

Request body: none

Response `200` as `application/json`:

Schema: `PublicWalletResponse`

```json
{
  "credits_available": {
    "amount": "123.45",
    "unit": "credits"
  },
  "current_period_end": null,
  "plan": "free",
  "status": "active"
}
```

## Error Responses

Failed HTTP responses use a public error envelope:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "The request did not match the public API contract."
  },
  "request_id": "req_example"
}
```

Stable public gateway error codes are:

- `unauthorized`
- `forbidden`
- `rate_limited`
- `validation_failed`
- `missing_idempotency_key`
- `insufficient_credits`
- `dependency_unavailable`
- `capacity_unavailable`
- `internal_error`
- `idempotency_conflict`
- `operation_expired`

The SDK maps known public error codes to typed exceptions where available and keeps future unknown safe error codes as `ZentureAPIError` without exposing API tokens, bearer headers, prompts, or other secrets in exception strings.
