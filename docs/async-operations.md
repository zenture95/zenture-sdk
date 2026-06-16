# Async Operations

Some zenture routes create asynchronous operations. The SDK exposes three usage
levels:

- `create(...)` or `create_operation(...)`: create an operation and return the
  initial `PublicOperationResponse`.
- `operations.wait(operation_id, ...)`: poll an existing operation until it is
  terminal.
- `.run(...)`: create an operation and wait for it with a single helper.

Terminal statuses are `succeeded`, `failed`, `cancelled`, and `expired`.
Non-terminal statuses are `queued` and `running`.

## Result Shape

`.run(...)` returns `OperationRunResult` with:

- `operation_id`
- `status`
- `result`
- `error`
- `idempotency_key`
- `last_request_id`

Failed terminal operations return `status="failed"` with an operation `error`.
They are not converted into response parsing failures.

## Timeout and Stop

`timeout` is a total local polling budget, not an HTTP read timeout. Sync
polling accepts `stop: Callable[[], bool] | None`. Async polling propagates
`asyncio.CancelledError` from task cancellation and accepts the same local stop
callable.

When create succeeds but local polling times out or is stopped, the exception
contains `operation_id` and `idempotency_key` attributes for recovery. These
attributes are not interpolated into exception strings.
