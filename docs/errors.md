# Errors

The SDK raises typed exceptions for public API errors and local SDK failures.
API errors include safe fields such as `error_code`, `status_code`,
`request_id`, and `retry_after` when available.

Common exception types:

- `ZentureAPIError`
- `ZentureAuthenticationError`
- `ZenturePermissionError`
- `ZentureValidationError`
- `ZentureMissingIdempotencyKeyError`
- `ZentureIdempotencyConflictError`
- `ZentureInsufficientCreditsError`
- `ZentureRateLimitError`
- `ZentureCapacityError`
- `ZentureDependencyUnavailableError`
- `ZentureInternalServerError`
- `ZentureOperationExpiredError`
- `ZentureTransportError`
- `ZentureResponseError`
- `ZenturePollingTimeoutError`
- `ZenturePollingStoppedError`

## Polling Errors

`ZentureInsufficientCreditsError` means the wallet has fewer than the public API
minimum required balance for paid AI operations. Call `client.wallet.get()` to
read the current plan and available credits before retrying.

`ZenturePollingTimeoutError` and `ZenturePollingStoppedError` may include
`operation_id`, `idempotency_key`, and `last_request_id` attributes. Use them to
resume an operation or retry safely with the same idempotency key.

## Evaluation Target Errors

`client.evaluations.create(...)` and `client.evaluations.run(...)` support two
different target modes:

- External evaluation: send `user_message`, `ai_answer`, optional
  `external_id`, and optional `metadata`. Omit `chat_id`, `turn_id`, and
  `model_response_id`.
- Internal zenture chat evaluation: send `user_message`, `ai_answer`, and the
  AI-answer `model_response_id`. `chat_id` and `turn_id` are optional
  correlation fields, but if either is present, `model_response_id` is required.

The SDK catches the common internal/external mix-up locally. Passing `chat_id`
or `turn_id` without `model_response_id` raises Pydantic `ValidationError`
before any HTTP request is sent. Server-side target validation, such as a
`model_response_id` that does not belong to the authenticated API user, raises
`ZentureValidationError` with `status_code == 422` and
`error_code == "validation_failed"`.

Do not treat this case as a terminal failed operation. A failed evaluation
operation means zenture accepted the request target and execution failed later;
a malformed internal-vs-external payload is a validation error.

## Redaction

Exceptions must not expose API tokens, Authorization headers, prompts, answers,
raw request bodies, raw response bodies, JWTs, provider payloads, or billing
internals. Do not add logs that print exception internals without considering
redaction.
