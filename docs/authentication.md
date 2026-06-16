# Authentication

`zenture-sdk` is server-side only. zenture API tokens are credentials for
trusted backend environments such as services, workers, automation jobs, CI, and
controlled notebooks.

Do not embed API tokens in browsers, mobile apps, frontend bundles, public
notebooks, logs, traces, analytics, screenshots, support tickets, or
customer-visible errors.

## Token Creation

Create API tokens in the existing zenture webapp with an existing account:
`https://ai.zenture.app/profile?tab=api-tokens`.

The SDK intentionally does not expose an API-token management surface for
creating, rotating, revoking, or auditing tokens.

## Environment Setup

Store tokens outside Python source code:

```bash
# .env, not committed
ZENTURE_API_KEY=your_webapp_created_api_token
```

```bash
set -a
. ./.env
set +a
```

Use `Zenture.from_env()` or `AsyncZenture.from_env()` so application code reads
the token from `ZENTURE_API_KEY`.

## Base URL

The production origin is `https://api.zenture.app`.

For controlled debugging only, `from_env()` also reads `ZENTURE_BASE_URL`.
Valid remote origins are:

- `https://api.zenture.app`
- `https://api-int.zenture.app`

Local `localhost`, `127.0.0.1`, and `[::1]` origins are accepted for local
debugging. Never derive `ZENTURE_BASE_URL` or constructor `base_url` values from
user input.
