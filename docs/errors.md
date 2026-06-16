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

`ZenturePollingTimeoutError` and `ZenturePollingStoppedError` may include
`operation_id`, `idempotency_key`, and `last_request_id` attributes. Use them to
resume an operation or retry safely with the same idempotency key.

## Redaction

Exceptions must not expose API tokens, Authorization headers, prompts, answers,
raw request bodies, raw response bodies, JWTs, provider payloads, or billing
internals. Do not add logs that print exception internals without considering
redaction.
