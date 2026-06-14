# PLAN_ZENTURE_SDK

## 1. Zielbild

`zenture-sdk` wird das offizielle öffentliche Python SDK fuer die zenture Public API. Das SDK richtet sich an serverseitige Integrationen: AI-Teams, Evaluation-Pipelines, Automations, Backend-Services, CI-Jobs und sichere Notebook-Umgebungen. Es soll wie ein professionelles Critical-Infra SDK wirken: strikt typisiert, deterministisch testbar, sicher im Umgang mit Secrets, klar versioniert und fuer externe Open-Source-Reviews nachvollziehbar.

Empfohlene Namen:

- GitHub Repository: `zenture-sdk`
- PyPI Distribution: `zenture-sdk`
- Python Import Name: `zenture`
- Sync Client: `Zenture`
- Async Client: `AsyncZenture`

Empfohlene Lizenz:

- `Apache-2.0` bleibt der Default.
- Begruendung: permissiv, OSS-kompatibel, enterprise-freundlich, mit expliziter Patentlizenz.
- Aktueller Repo-Zustand: `LICENSE` enthaelt bereits Apache License 2.0.
- Vor Public Go-Live muss ein `NOTICE` mit zenture Copyright und relevanten Drittanbieter-Hinweisen ergaenzt werden.

## 2. Nicht-Ziele

V1 des SDK implementiert keine Browser-, Mobile- oder Frontend-Nutzung. zenture API Tokens sind serverseitige Secrets und duerfen nicht in Client Bundles, mobile Apps, public Notebooks, Logs oder Error Reports gelangen.

Nicht im SDK enthalten:

- API-Token-Erstellung, Rotation, Revocation und Audit ueber `/v1/api-tokens`.
- OAuth, Organization Tokens, API Wallets oder Service Accounts.
- WebSocket/SSE Streaming.
- Payment-Mutationen, Checkout, Stripe- oder Zahlungsdaten.
- Direkte Backend-Routen oder interne Gateway/Backend Service APIs.
- INT/PROD Deployment, Gateway- oder Backend-Aenderungen.

Geklaerte Produktentscheidung: API Tokens werden in V1 ausschliesslich ueber die bestehende Webapp mit bestehendem Account erstellt und verwaltet. Das SDK nutzt nur bereits erzeugte API Tokens.

## 3. Analysierter Kontext

Repo-Zustand `zenture-sdk`:

- Vorhanden: `README.md`, `LICENSE`, `.gitignore`.
- Keine Implementierung, kein `pyproject.toml`, keine Package-Struktur.
- Keine lokalen Git-Aenderungen vor Erstellung dieses Plans.

Relevante Plattformquellen:

- `zenture-api-gateway/docs/PLAN_PUBLIC_API_GATEWAY.md`
- `zenture-api-gateway/docs/SDK_AND_DEVELOPER_EXPERIENCE.md`
- `zenture-api-gateway/openapi/zenture-public-api-v1.openapi.json`
- Public docs unter `zenture-api-gateway/docs/public/`

OpenAPI Stand:

- OpenAPI: `3.1.0`
- Contract Version: `1.0.0-rc.2`
- Server:
  - `https://api.zenture.app`
  - `https://api-int.zenture.app`
- Public API Base Path: `/v1`

V1 API-token Routen im aktuellen OpenAPI-Artefakt:

- `GET /v1/helloworld`
- `POST /v1/chat`
- `POST /v1/input-wizard`
- `POST /v1/evaluate` geplant und V1-pflichtig, aber im aktuellen `1.0.0-rc.2` Artefakt noch nicht enthalten
- `GET /v1/operations/{operation_id}`
- `GET /v1/chats`
- `GET /v1/chats/{chat_id}`
- `GET /v1/chats/{chat_id}/messages`
- `GET /v1/evaluations`
- `GET /v1/evaluations/{evaluation_id}`
- `GET /v1/billing`
- `GET /v1/usage`
- `GET /v1/limits`

Contract-Gap vor SDK Beta:

- Der Plattformplan fordert Beispiele und API-Scope fuer `POST /evaluate`.
- Das aktuelle OpenAPI-Artefakt `1.0.0-rc.2` enthaelt `GET /evaluations` und `GET /evaluations/{evaluation_id}`, aber kein `POST /evaluate`.
- Finale Entscheidung: `POST /v1/evaluate` muss in V1 rein. Evaluation-Create ist ein Kernworkflow/USP und wird vor SDK-Beta in Gateway, Backend und OpenAPI ergaenzt.
- SDK-seitig wird Evaluation-Create erst gegen den finalisierten OpenAPI-Contract implementiert, sobald `POST /v1/evaluate` vorhanden ist.
- SDK Beta darf nicht shippen, solange Evaluation-Create im finalen Contract fehlt oder das SDK ihn nicht korrekt abbildet.

## 4. Empfohlene Architektur

Das SDK besteht aus drei Schichten:

1. Handwritten public ergonomic layer
2. Shared transport/runtime layer
3. Generated OpenAPI contract layer unter internem Namespace

Die handgeschriebene Schicht ist die stabile Public API. Generated Code wird als Implementierungsdetail behandelt und nicht prominent exportiert.

Empfohlenes Prinzip:

- Generated layer liefert rohe operationId-nahe Methoden, Schemas oder request/response Hilfen.
- Handwritten resources liefern ergonomische Methoden, Idempotency UX, Polling, Retry, typed errors, Redaction und Beispiele.
- Sync und Async teilen Modelle, Error Mapping, Rate-Limit Parsing, Idempotency, Polling-Policy und Retry-Entscheidungen.
- Transport-Lebenszyklus ist explizit: Clients sind Context Manager und haben `close()` beziehungsweise `aclose()`.

## 5. Ordnerstruktur

```text
zenture-sdk/
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── LICENSE
├── NOTICE
├── PLAN_ZENTURE_SDK.md
├── pyproject.toml
├── ruff.toml
├── pyrightconfig.json
├── src/
│   └── zenture/
│       ├── __init__.py
│       ├── py.typed
│       ├── _version.py
│       ├── client.py
│       ├── async_client.py
│       ├── config.py
│       ├── errors.py
│       ├── idempotency.py
│       ├── logging.py
│       ├── models.py
│       ├── pagination.py
│       ├── polling.py
│       ├── rate_limits.py
│       ├── redaction.py
│       ├── retries.py
│       ├── types.py
│       ├── transport/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── sync.py
│       │   └── async_.py
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── billing.py
│       │   ├── chat.py
│       │   ├── evaluations.py
│       │   ├── helloworld.py
│       │   ├── input_wizard.py
│       │   ├── limits.py
│       │   ├── operations.py
│       │   └── usage.py
│       └── _generated/
│           ├── __init__.py
│           └── ...
├── openapi/
│   ├── zenture-public-api-v1.openapi.json
│   └── README.md
├── examples/
│   ├── helloworld.py
│   ├── input_wizard.py
│   ├── chat.py
│   ├── async_chat.py
│   ├── operation_polling.py
│   ├── idempotency.py
│   ├── error_handling.py
│   └── usage_report.py
├── docs/
│   ├── authentication.md
│   ├── api-reference.md
│   ├── async-operations.md
│   ├── errors.md
│   ├── idempotency.md
│   ├── migration.md
│   ├── rate-limits.md
│   ├── release.md
│   └── security.md
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── examples/
│   └── fixtures/
│       ├── http/
│       └── openapi/
└── .github/
    ├── CODEOWNERS
    └── workflows/
        ├── ci.yml
        ├── release.yml
        └── scorecard.yml
```

Module size targets:

- Handwritten Python modules should stay below 250 LOC where practical.
- Resource modules may grow to 300 LOC only when sync/async wrappers remain shallow.
- Generated files are exempt but must live only under `zenture._generated`.

## 6. Python Version Und Packaging

Empfehlung: Python `3.11+`.

Begruendung:

- Plattformplan empfiehlt Python `3.11+`, passend zur Backend Runtime.
- Bessere Typing-Ergonomie als 3.10.
- Reduziert Support-Matrix fuer ein junges Critical-Infra SDK.
- Python 3.11 ist fuer aktuelle AI/Data/Backend-Umgebungen breit verfuegbar.

`pyproject.toml` Anforderungen:

- Build Backend: `hatchling` oder `pdm-backend`; Empfehlung `hatchling` wegen schlanker Library-Packaging UX.
- `requires-python = ">=3.11"`
- SPDX License: `Apache-2.0`
- Runtime Dependencies:
  - `httpx>=0.27,<1`
  - `pydantic>=2.7,<3`
  - `typing-extensions>=4.10` falls noetig
- Optional Dev Dependencies:
  - `pytest`
  - `pytest-asyncio`
  - `respx`
  - `coverage[toml]`
  - `ruff`
  - `mypy`
  - `pyright`
  - `build`
  - `twine`
  - `openapi-spec-validator` oder `vacuum/spectral` im CI

Das Package muss `py.typed` shippen.

## 7. Public SDK API

Primary usage:

```python
import os

from zenture import Zenture

client = Zenture(api_key=os.environ["ZENTURE_API_KEY"])

message = client.helloworld()
print(message)
```

Context-manager usage:

```python
import os

from zenture import Zenture

with Zenture(api_key=os.environ["ZENTURE_API_KEY"]) as client:
    result = client.input_wizard.run(
        prompt="Draft a concise onboarding prompt for a support chatbot.",
        idempotency_key="ticket-428-input-wizard-v1",
    )
```

Async usage:

```python
import os

from zenture import AsyncZenture

async with AsyncZenture(api_key=os.environ["ZENTURE_API_KEY"]) as client:
    result = await client.chat.run(
        message="Summarize the security posture of this architecture.",
        timeout=120.0,
    )
```

Low-level operation creation:

```python
from zenture import Zenture

client = Zenture.from_env()

operation = client.chat.create_operation(
    message="Review this API design.",
    idempotency_key="customer-123-chat-design-review-001",
    wait=False,
)

result = client.operations.wait(
    operation.operation_id,
    timeout=120.0,
    poll_interval=2.0,
)
```

Idempotency:

```python
from zenture import Zenture
from zenture.idempotency import idempotency_key

client = Zenture.from_env()

key = idempotency_key("order-123", "chat", "v1")

operation = client.chat.create_operation(
    message="Create a product summary.",
    idempotency_key=key,
)
```

Error handling:

```python
from zenture import Zenture
from zenture.errors import (
    ZentureAPIError,
    ZentureRateLimitError,
    ZentureValidationError,
)

client = Zenture.from_env()

try:
    client.chat.create_operation(
        message="hello",
        idempotency_key="example-chat-001",
    )
except ZentureRateLimitError as exc:
    print(exc.request_id)
    print(exc.retry_after)
except ZentureValidationError as exc:
    print(exc.error_code)
except ZentureAPIError as exc:
    print(exc.request_id)
```

Evaluation examples:

```python
from zenture import Zenture

client = Zenture.from_env()

evaluation = client.evaluations.get("eval_abc123")
```

Evaluation create/run is V1-pflichtig, but implementation is gated on final OpenAPI support for `POST /v1/evaluate`:

```python
result = client.evaluations.run(
    user_message="What is SOC 2?",
    ai_answer="SOC 2 is a compliance framework...",
    idempotency_key="case-123-eval-001",
    timeout=120.0,
)
```

The create/run evaluation API must not be implemented until the OpenAPI contract exposes the route. Once present, SDK Beta must include it.

`.run()` return shape:

```python
operation_result = client.chat.run(
    message="Summarize this incident report.",
    timeout=120.0,
)

print(operation_result.operation_id)
print(operation_result.status)
print(operation_result.idempotency_key)
print(operation_result.last_request_id)
print(operation_result.result)
```

`.run()` never returns a naked domain answer in V1. It returns a bounded operation result wrapper with at least `operation_id`, `status`, `result`, `idempotency_key`, and optional `request_id`/`last_request_id`.

## 8. Sync vs Async Entscheidung

Empfehlung: beide Clients in V1.

Gruende:

- Sync ist ergonomisch fuer Scripts, CI, notebooks, CLI-artige Automations und einfache backend jobs.
- Async ist wichtig fuer Services, Worker, FastAPI/asyncio Integrationen und parallele Operation-Polling Workloads.
- Der Plattformplan fordert beide.

Design-Regeln:

- `Zenture` nutzt `httpx.Client`.
- `AsyncZenture` nutzt `httpx.AsyncClient`.
- Keine duplizierte Business-Logik fuer Fehler, Retry, Rate Limits, Redaction, Polling oder Idempotency.
- Sync/Async Resource-Klassen duerfen duenne Wrapper haben, aber Policies leben in gemeinsamen kleinen Modulen.
- Beide Clients unterstuetzen explizites `close()`/`aclose()` und Context Manager.
- Extern bereitgestellte `httpx.Client`/`httpx.AsyncClient` Instanzen werden nicht ungefragt geschlossen; SDK-eigene Clients werden geschlossen.

## 9. Generated Client vs Handwritten Layer

Empfehlung: hybrider Ansatz.

Generated:

- OpenAPI Artefakt wird in `openapi/zenture-public-api-v1.openapi.json` im SDK Repo gespiegelt.
- Generated Code lebt unter `zenture._generated`.
- Generated Code ist intern und wird nicht als primäre API dokumentiert.
- Regeneration muss deterministisch sein und in CI geprueft werden.
- Generated Typen duerfen als Grundlage dienen, wenn sie Pydantic v2 und striktes Typing sauber unterstuetzen.

Handwritten:

- `Zenture`, `AsyncZenture`, Resources, Polling, Errors, Redaction, Retry und Idempotency bleiben handgeschrieben.
- Public API Namen sollen produktnah sein, nicht operationId-nah.
- Der handwritten Layer glättet Gateway-Details, ohne Contract-Semantik zu verstecken.

Tooling-Entscheidung vor Implementierung:

- Kandidaten pruefen: `openapi-python-client`, `datamodel-code-generator`, eigener minimaler Generator fuer Pydantic Models.
- Entscheidungskriterium: Typqualitaet, Pydantic v2 Support, deterministische Diffs, geringe Dependency-Last, gute Kontrolle ueber Public API.
- Wenn Generator-Output zu gross oder instabil ist, nur Pydantic Models generieren und Transport handschreiben.

Generator-Evaluation:

| Option | Vorteil | Risiko | Vorlaeufige Bewertung |
| --- | --- | --- | --- |
| `openapi-python-client` | Vollstaendiger Client aus OpenAPI, schnelle Abdeckung vieler Operationen | Output kann zu viel Public Surface erzeugen, Sync/Async Ergonomie und Pydantic-v2-Qualitaet muessen kritisch geprueft werden | Nur nutzen, wenn Output reviewbar, stabil und klar intern isolierbar ist |
| `datamodel-code-generator` | Gut fuer contract-derived Pydantic Models, Transport bleibt kontrolliert handgeschrieben | Liefert keinen ergonomischen Client; zusaetzliche Glue-Schicht noetig | Gute Default-Tendenz fuer Models, wenn Output klein und deterministisch bleibt |
| Eigener minimaler Generator | Maximale Kontrolle, minimale Public Surface, exakt auf zenture Contract zugeschnitten | Wartungsaufwand und Generator-Bugs liegen komplett bei zenture | Gute Option, wenn nur Models/Enums/contract checks noetig sind |

Aktuelle Empfehlung: handwritten ergonomic SDK plus Pydantic Models plus contract-derived checks. Ein Generator wird nur eingesetzt, wenn sein Output klein, deterministisch, typstark und fuer externe Reviews gut lesbar bleibt.

## 10. Pydantic Models Und Typing

Pydantic v2 ist Pflicht fuer Request/Response Models.

Model-Regeln:

- `model_config = ConfigDict(extra="forbid", frozen=True)` fuer public response/value models, soweit sinnvoll.
- Keine Secrets in `repr`.
- API Key wird nicht als Pydantic-Feld mit normalem repr modelliert.
- DateTimes als timezone-aware `datetime`.
- Public IDs als constrained/newtype-artige Aliases:
  - `ChatId`
  - `EvaluationId`
  - `OperationId`
  - `RequestId`
  - `ApiTokenId` nur falls metadata gebraucht wird, nicht fuer Token-Management Surface.
- Operation Status als `Literal` oder `StrEnum`.
- Error Codes als `StrEnum` plus Unknown-Fallback fuer Forward Compatibility.

OpenAPI aktuell bekannte Operation Statuses:

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`
- `expired`

OpenAPI aktuell bekannte Error Codes:

- `unauthorized`
- `forbidden`
- `rate_limited`
- `validation_failed`
- `missing_idempotency_key` geplant als stabiler V1 Error Code mit HTTP `400`
- `dependency_unavailable`
- `capacity_unavailable`
- `internal_error`
- `idempotency_conflict`
- `operation_expired`

Error-Code Entscheidung:

- Fehlender `Idempotency-Key` bekommt einen stabilen Error Code `missing_idempotency_key` mit HTTP `400`.
- `validation_failed` bleibt fuer sonstige Body-, Path-, Query- und Header-Validation.
- OpenAPI, Gateway, Docs und SDK muessen diesen Error Code vor SDK Beta konsistent enthalten.

## 11. HTTPX Nutzung

`httpx` ist der einzige HTTP Transport.

Client Optionen:

```python
Zenture(
    api_key: str | None = None,
    base_url: str = "https://api.zenture.app",
    timeout: float | httpx.Timeout | None = None,
    transport: httpx.BaseTransport | None = None,
    user_agent: str | None = None,
    max_retries: int = 2,
)
```

Defaults:

- `base_url`: `https://api.zenture.app`
- `timeout`: connect `5s`, read/write/pool `30s`; long operation waiting uses polling timeout, not HTTP read timeout.
- `User-Agent`: `zenture-sdk-python/{sdk_version} python/{major.minor} openapi/{contract_version}`
- Headers:
  - `Authorization: Bearer <api_key>`
  - `Content-Type: application/json` for JSON requests
  - `Idempotency-Key` only when required/provided

Rules:

- No API key in URL.
- No automatic environment lookup except `Zenture.from_env()`.
- `from_env()` reads `ZENTURE_API_KEY`.
- `ZENTURE_BASE_URL` may be supported only for local debugging and INT usage. Public docs must state that base URLs must never come from user input.
- Base URL validation rejects obvious frontend/backend internal paths by default.
- The SDK appends the versioned `/v1` API path internally unless a final transport design explicitly stores `base_url` as the versioned API root. Public examples should use the production origin `https://api.zenture.app`.
- Tests use `respx` or `httpx.MockTransport`; no network by default.

## 12. Error-Modell

Base exception:

```python
class ZentureError(Exception): ...
class ZentureAPIError(ZentureError): ...
```

Typed API errors:

- `ZentureAuthenticationError` for `unauthorized`
- `ZenturePermissionError` for `forbidden`
- `ZentureValidationError` for `validation_failed`
- `ZentureMissingIdempotencyKeyError` for `missing_idempotency_key`
- `ZentureIdempotencyConflictError` for `idempotency_conflict`
- `ZentureRateLimitError` for `rate_limited`
- `ZentureCapacityError` for `capacity_unavailable`
- `ZentureDependencyUnavailableError` for `dependency_unavailable`
- `ZentureInternalServerError` for `internal_error`
- `ZentureOperationExpiredError` for `operation_expired`
- `ZentureTransportError` for client-side network/timeout errors
- `ZentureResponseError` for invalid JSON or contract mismatch

Exception fields:

- `message`
- `error_code`
- `status_code`
- `request_id`
- `retry_after`
- `rate_limit`
- `response_headers` redacted/safe subset only

Forbidden in exceptions:

- API tokens
- Authorization headers
- prompts
- model answers
- raw request bodies
- raw response bodies
- JWTs
- provider payloads
- billing internals

Unknown future error codes:

- Preserve raw code as string.
- Raise `ZentureAPIError`, not a generic `ValueError`.
- Include `request_id` and HTTP status.

## 13. Polling Helpers Fuer Async Operations

High-level `.run()` helpers:

- Create operation.
- Poll until terminal status.
- Return a typed `OperationRunResult`, never a naked domain answer.
- Auto-generate an idempotency key only when the method is explicitly high-level and exposes generated metadata.
- Include at least `operation_id`, `status`, `result`, `idempotency_key`, and optional `request_id`/`last_request_id`.

Operation result typing:

- V1 uses safe-ref-first result typing.
- `PublicOperationResult` is bounded and typed, but intentionally does not expose rich inline domain-specific payloads until OpenAPI defines clear domain-specific result unions.
- The result should contain safe references and compact status metadata such as public `chat_id`, `evaluation_id`, timestamps, or summary fields allowed by the public contract.
- The SDK must not guess or widen result payloads from arbitrary JSON.
- Rich inline domain results can be added later as a backwards-compatible minor release only after OpenAPI provides explicit result unions.

Low-level `.create_operation()` helpers:

- Require explicit `idempotency_key` for mutating async routes.
- Return `Operation`.
- Caller controls polling.

Polling defaults:

- Initial interval: `1.0s`
- Max interval: `8.0s`
- Jitter: full or decorrelated jitter, bounded.
- Timeout: caller-provided; recommended examples use `120s`.
- Stop on terminal statuses: `succeeded`, `failed`, `cancelled`, `expired`.
- Honor `Retry-After` and `RateLimit-Reset`.
- Treat 429 during polling as retryable with server-guided wait.
- Treat `operation_expired` as terminal non-retryable.

Cancellation:

- Sync polling accepts a `stop: Callable[[], bool] | None`.
- Async polling accepts cooperative cancellation via task cancellation and optional async stop callback.
- If local polling is cancelled, SDK does not imply server-side cancellation unless a future API adds a cancellation endpoint.

## 14. Idempotency-Key UX

Rules:

- Mutating async routes require `Idempotency-Key`.
- SDK never retries billable or mutating `POST` unless an idempotency key is present.
- Low-level create methods require caller-provided keys.
- High-level run methods may generate keys for convenience, but must expose the generated key in metadata or result wrapper.
- Idempotency keys must not contain prompts, answers, tokens, customer PII or raw request bodies.

Helper:

```python
from zenture.idempotency import idempotency_key

key = idempotency_key("customer-123", "chat", "2026-06-14T12:00:00Z")
```

Implementation:

- Validate key length and allowed characters once OpenAPI/header constraints are final.
- Provide `IdempotencyKey` type alias.
- Do not hash keys silently; users need stable keys for support and replay correlation.
- Docs should recommend caller-owned business IDs and stable operation IDs.

## 15. Pagination Und Iterators

Final V1 pagination contract before SDK Beta:

- Query params: `limit`, `cursor`.
- Response field: `next_cursor`.
- Default sort: `created_at desc`.
- Maximum `limit`: `100`.
- Recommended default `limit`: `50`.

Default `50` is the best tradeoff for the SDK: it keeps API usage efficient for normal chat/evaluation lists while still bounding payload size and memory pressure. For message-heavy resources or later richer result payloads, individual resource methods may choose a lower documented default only if OpenAPI encodes that route-specific default.

SDK helpers:

- List methods accept `limit: int | None = None` and `cursor: str | None = None`.
- List methods return typed page objects with `items` and `next_cursor`.
- Resource clients expose sync and async paginator helpers:
  - `client.chats.list_pages(limit=50)`
  - `client.chats.iter(limit=50)`
  - `async for chat in client.chats.aiter(limit=50): ...`
- Iterators must be lazy and stop when `next_cursor` is absent.
- Iterators must not hide API errors or rate limits.
- Tests must cover page boundaries, empty pages, max-limit validation, and cursor propagation.

## 16. Retry, Timeout Und Backoff Policy

Retryable by default:

- `GET` requests on transient network errors.
- `GET /v1/operations/{operation_id}` polling.
- 429 with `Retry-After`.
- 503 for `dependency_unavailable` or `capacity_unavailable`.
- 500 `internal_error` only for idempotent reads or idempotent POSTs with key.

Not retryable by default:

- 400/401/403/409/410/413/422/431.
- `missing_idempotency_key`.
- Any mutating POST without idempotency key.
- Contract mismatch or invalid response shape.

Backoff:

- Exponential backoff with jitter.
- Cap per-attempt sleep.
- Respect server `Retry-After` over client guess.
- Expose retry metadata only in debug-safe form.

Timeouts:

- HTTP request timeout is separate from operation polling timeout.
- `run(timeout=...)` means total operation wait budget, not raw HTTP read timeout.
- Create request may pass `wait=false` or `wait=0` for immediate async behavior when supported by contract.

## 17. Redaction Und Secret Handling

Non-negotiable:

- API token never appears in logs, exceptions, repr, test snapshots or debug output.
- Authorization header is always redacted as `<redacted>`.
- Request/response bodies are not logged by default.
- Prompt and model-answer text are considered sensitive content.
- Billing/payment payloads are considered sensitive.
- Examples load tokens from env vars only.
- Fixtures use fake tokens such as `zt_test_redacted_000000`.

Public object repr:

- Client repr: `Zenture(base_url='https://api.zenture.app/v1', api_key='<redacted>')`
- Errors: include `request_id`, `status_code`, `error_code`, safe message.
- No raw `httpx.Request` or `httpx.Response` repr in thrown exceptions.

Debug hooks:

- Opt-in only.
- Redacted by default.
- Must have redaction regression tests.

## 18. Logging Policy

Default SDK behavior:

- No logging.
- No stdout/stderr writes.
- No `print`.

If logging is added:

- Use Python `logging`.
- Logger name: `zenture`.
- Emit metadata only: method, route template, status code, request_id, elapsed_ms, retry_count.
- Do not log path params if they could contain unsafe data except validated public IDs.
- Do not log headers except safe allowlist.
- Do not log request or response bodies.

## 19. Testing Strategie

Unit tests:

- Error mapping per public error code.
- Rate-limit header parsing.
- Retry decision matrix.
- Idempotency key validation/generation.
- Redaction helpers.
- Pydantic model validation.
- Base URL and config validation.
- Sync/async close semantics.

Mocked HTTP integration tests:

- `helloworld`
- `input_wizard.create_operation`
- `input_wizard.run`
- `chat.create_operation`
- `chat.run`
- `evaluations.create_operation`
- `evaluations.run`
- `operations.wait`: success, failed, cancelled, expired, timeout
- `GET /chats`, chat detail, messages
- `GET /evaluations`, evaluation detail
- `GET /billing`, `GET /usage`, `GET /limits`
- 400/401/403/409/410/429/503 mapping
- `missing_idempotency_key` mapping to `ZentureMissingIdempotencyKeyError`
- `Retry-After` handling
- Idempotency conflict
- No retry without idempotency key
- Pagination page and iterator behavior for `limit`, `cursor`, `next_cursor`, max `100`

Contract tests:

- Committed OpenAPI version matches SDK metadata.
- Generated layer is in sync with committed OpenAPI.
- SDK examples only call endpoints present in OpenAPI.
- Error code enum matches OpenAPI plus documented unknown fallback.
- Operation status enum matches OpenAPI.
- `POST /v1/evaluate` is present before SDK Beta and mapped by evaluation create/run helpers.
- `missing_idempotency_key` is present before SDK Beta and maps to the typed SDK error.
- Routes requiring idempotency in OpenAPI require keys in SDK low-level methods.
- Pagination defaults and max limits match OpenAPI/docs.
- `user_session` endpoints are excluded from API-token SDK surface.

Example tests:

- Run examples against mocked fixtures.
- Assert no real network.
- Assert examples never print tokens.

Security regression tests:

- API key absent from exception string and repr.
- Authorization redacted from debug metadata.
- Prompt text absent from errors when server returns failure.
- No fixture contains real-looking production tokens.

Coverage and determinism:

- Minimum line coverage: `90%` for handwritten SDK code.
- Branch coverage target: `85%`.
- Generated code excluded from coverage gate but regeneration checked.
- Tests default to no network.
- No tests require real zenture credentials.

## 20. Static Quality

Recommended tools:

- Ruff for linting, formatting and import sorting.
- Mypy `--strict`.
- Pyright in strict mode for public API verification.
- Pytest with coverage.

Ruff target:

- `line-length = 100`
- Python target: `py311`
- Enable `E`, `F`, `I`, `B`, `UP`, `SIM`, `C4`, `PT`, `RUF`, `TCH`, `RET`, `PTH`, `TRY` selectively.

Typing rules:

- Public methods fully typed.
- No `Any` in public API signatures except explicit JSON escape hatches.
- `py.typed` included.
- Public exports controlled in `zenture/__init__.py`.
- Generated code can have relaxed typing only under `_generated` with documented exceptions.

## 21. CI/CD Und Release Plan

GitHub Actions:

- `ci.yml`
  - Ruff format check
  - Ruff lint
  - Mypy strict
  - Pyright
  - Pytest with coverage
  - Contract drift check
  - Example tests
  - Build package
  - Twine check
- `release.yml`
  - Triggered by signed/tagged release or protected GitHub release flow.
  - Uses PyPI Trusted Publishing via OIDC.
  - No long-lived PyPI token.
  - Produces sdist and wheel.
  - Publishes provenance/attestations where supported.
- `scorecard.yml`
  - OpenSSF Scorecard.

Repository governance gates:

- GitHub repository exists under the zenture organization before SDK implementation starts.
- Repository remains private until the SDK is final, security-reviewed, and explicitly approved for public release.
- Public release must not expose the private development commit history.
- `CODEOWNERS` is present and protects SDK maintainers/release owners.
- Branch protection or GitHub rulesets are enabled for the default branch.
- Required PR review is enabled before feature work starts.
- Required CI checks are enforced as soon as `ci.yml` exists.
- Direct pushes to the default branch are blocked after initial bootstrap.
- Secret scanning and push protection are enabled before any API examples or docs are added.
- Dependabot or Renovate is enabled before runtime dependencies are introduced.
- Actions default permissions are read-only before release workflows are added.
- Protected GitHub environments exist for `testpypi` and `pypi` before publishing workflows are enabled.
- PyPI name `zenture-sdk` is reserved/verified before public package publication; passive Pending Publisher setup alone is not treated as name reservation.
- PyPI Trusted Publishing is configured before any public PyPI release.

Least privilege:

- Default Actions permissions: read-only.
- Release job grants only required `id-token: write` and package publishing permissions.

Prerelease:

- Internal prerelease versions: `0.1.0aN` or `0.1.0rcN`.
- Target OpenAPI release candidate, e.g. `1.0.0-rc.N`.
- First distribution is an internal wheel/GitHub Actions artifact.
- TestPyPI is optional after package metadata freeze.
- Public PyPI beta is allowed only after the SDK reviewer gate passes.
- Stable PyPI release is allowed only after public go-live checklist passes.

Public Go-Live:

- Public repository is created from a clean reviewed tree snapshot, not from the private development history.
- Public initial commit contains only approved release files and no private planning churn, experiments, deleted files, secrets, generated temp files, local artifacts, or sensitive metadata.
- Existing private history is not made public. If the same GitHub repository is converted to public, its default branch must first be replaced by a clean orphan history and all non-release branches/tags must be removed before visibility changes.
- Because published Git history cannot be reliably deleted from every clone/cache after exposure, the safe rule is: never make the private history public.
- SDK release references exact OpenAPI contract version.
- Changelog includes breaking/feature/fix sections.
- GitHub Release links docs, OpenAPI artifact, provenance and migration notes.

## 22. Docs Struktur

README must include:

- Copy-paste install command.
- Copy-paste quickstart.
- Server-side token warning.
- `ZENTURE_API_KEY` env var setup.
- Sync and async minimal examples.
- Idempotency example.
- Polling example.
- Error handling example.
- Link to docs and API reference.
- Supported Python versions.
- License.

Docs:

- `docs/authentication.md`
- `docs/idempotency.md`
- `docs/async-operations.md`
- `docs/errors.md`
- `docs/rate-limits.md`
- `docs/api-reference.md`
- `docs/security.md`
- `docs/migration.md`
- `docs/release.md`

Examples required before Beta:

- Client initialisieren
- `helloworld`
- `input_wizard`
- `chat`
- Operation polling
- Idempotency
- Error handling
- `usage`/billing read
- Async chat
- Evaluation create/run, once `POST /v1/evaluate` is present in the final OpenAPI contract

Evaluation create example is mandatory for SDK Beta, but implementation remains gated on final OpenAPI support for `POST /v1/evaluate`.

## 23. Versioning Und Contract Alignment

Use SemVer for SDK:

- `MAJOR`: breaking public SDK API change or breaking supported OpenAPI contract.
- `MINOR`: new endpoints/helpers, backwards-compatible models, new resource methods.
- `PATCH`: bugfixes, docs, improved typing without breaking behavior.
- Pre-1.0 may still break, but public prerelease must document instability clearly.

Contract alignment:

- SDK embeds target OpenAPI contract version.
- SDK CI fails if generated code differs from committed OpenAPI.
- SDK docs must not mention routes absent from OpenAPI except in explicit roadmap/open-question sections.
- Breaking OpenAPI changes require SDK major or coordinated prerelease.
- Additive OpenAPI changes may ship as SDK minor.

## 24. Security Posture Fuer Public SDK

Security baseline:

- No secrets in logs, exceptions, reprs, tests, fixtures, snapshots, docs output.
- No automatic token persistence.
- No browser/mobile support claims.
- No telemetry.
- No dependency on shelling out.
- Minimal runtime dependencies.
- Dependency audit in CI.
- Secret scanning enabled on public repo.
- Responsible disclosure policy in `SECURITY.md`.
- Supply-chain release via Trusted Publishing and provenance.

Threats the SDK must explicitly mitigate:

- User accidentally committing examples with real tokens.
- Token leak via exception message.
- Prompt leak via debug logging.
- Retrying billable mutation without idempotency.
- Tight polling loops causing rate-limit pressure.
- Contract drift causing unsafe parsing or incorrect behavior.
- Async client not closing connections.

## 25. Review-Gate Vor Beta

Before prerelease, run a skeptical senior software/security review. Findings must be triaged:

- `must_fix_before_prerelease`
- `fix_before_public_go_live`
- `post_v1`

Concrete criteria:

- Architecture: clean separation between public API, transport, generated code and resources.
- Modularity: small modules, no shared mega-client, no circular imports.
- Generated code: isolated, deterministic, not leaked as primary public surface.
- Sync/Async: shared policies, no divergent behavior.
- Transport: lifecycle, timeouts, connection reuse and caller-provided clients correct.
- Errors: stable mapping, request IDs, rate-limit metadata, unknown-code fallback.
- Idempotency: no unsafe retry, clear low-level/high-level split.
- Polling: terminal statuses, timeout, cancellation, jitter, 429 handling.
- Redaction: tokens/prompts/bodies absent from all exceptions/logs/debug output.
- Tests: deterministic, mocked HTTP, no real tokens, examples tested.
- Static quality: Ruff, mypy strict, Pyright, coverage gates pass.
- Packaging: metadata, `py.typed`, sdist/wheel, README rendering.
- Release security: branch protection, Trusted Publishing, provenance, least-privilege Actions.
- Docs: quickstart is copy-pasteable and does not imply browser/mobile safety.

Exit criteria:

- Zero `must_fix_before_prerelease`.
- All `fix_before_public_go_live` either fixed or explicitly deferred with owner and rationale.
- Public API examples match committed OpenAPI.

## 26. Implementierungsphasen

Phase 0A: Repository governance bootstrap

This phase is intentionally pulled forward before SDK implementation. It creates the clean operating envelope for all later code work.

- Create or move the GitHub repository under the zenture organization.
- Keep repository private during bootstrap and implementation.
- Add `LICENSE`, `NOTICE`, `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, and `.github/CODEOWNERS`.
- Enable branch protection or rulesets on the default branch.
- Require pull requests and CODEOWNER review for protected paths.
- Block force-pushes and branch deletion on the default branch.
- Set GitHub Actions default token permissions to read-only.
- Enable secret scanning and push protection.
- Add Dependabot or Renovate config.
- Add placeholder `ci.yml` with at least formatting/lint/test jobs once project files exist, then make it required.
- Create protected GitHub environments `testpypi` and `pypi`; require manual approval for `pypi`.
- Configure Trusted Publishing only after release workflow identity is known.
- Verify `zenture-sdk` remains available on PyPI; do not publish a dummy package solely for name reservation.

Phase 0B: Contract decision checkpoint

- Verify `POST /v1/evaluate` is present in the finalized OpenAPI contract before SDK Beta.
- Verify final OpenAPI error code catalog includes `missing_idempotency_key`.
- Confirm OpenAPI idempotency header constraints.
- Verify package name availability on PyPI again before public package publication.
- Verify repository governance bootstrap is complete before SDK feature implementation.

Phase 1: Repo foundation

- Add `pyproject.toml`, `ruff.toml`, `pyrightconfig.json`.
- Add `src/zenture`, `py.typed`, version module.
- Add docs skeleton, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `NOTICE`.
- Add/activate CI skeleton and required checks.

Phase 2: Core runtime

- Implement config, redaction, errors, rate-limit parsing, retry policy, idempotency helpers.
- Implement sync/async transport with httpx.
- Add unit tests for all core policies.

Phase 3: Models and generated layer

- Copy locked OpenAPI artifact into `openapi/`.
- Select generator.
- Generate or handcraft Pydantic model baseline.
- Add regeneration and contract drift checks.

Phase 4: Resource clients

- Implement `helloworld`.
- Implement `operations`.
- Implement `chat`.
- Implement `input_wizard`.
- Implement evaluation create/run once `POST /v1/evaluate` is in the final OpenAPI contract.
- Implement read resources: chats, evaluations, billing, usage, limits.
- Exclude API-token management routes.

Phase 5: Polling, retries and idempotent run helpers

- Implement `.run()` helpers.
- Implement operation wait semantics.
- Add timeout/cancellation/rate-limit tests.

Phase 6: Docs and examples

- Write README quickstart.
- Add examples and mocked example tests.
- Write API docs and security docs.

Phase 7: Critical review gate

- Run review using criteria above.
- Fix all prerelease blockers.
- Verify static quality, package build and no-network tests.

Phase 8: Prerelease readiness

- Internal wheel/GitHub Actions artifact.
- Optional TestPyPI dry run after package metadata freeze.
- Trusted Publishing verification.
- Release checklist.
- Public PyPI beta only after SDK reviewer gate.
- Internal prerelease only after platform rollout gate approves SDK testing.

Phase 9: Public release history hygiene

This phase is mandatory before the repository is made public. The goal is to ensure external users see only a clean, reviewed release history.

- Freeze implementation after SDK reviewer gate.
- Run a final secret scan across the full private repository history.
- Run a final artifact scan for local caches, generated temp files, private notes, credentials, tokens, customer data, `.env` files, build outputs, and unreviewed OpenAPI artifacts.
- Create a clean export from the reviewed working tree.
- Prefer creating a fresh public repository under the zenture organization from that clean export.
- If the existing private GitHub repository must be reused, create an orphan release branch with a single initial public commit, make it the default branch, delete all old branches and tags from the remote, and only then change visibility to public.
- Do not rely on history rewrite as a cleanup mechanism after public exposure. If sensitive history was ever public, treat it as disclosed and rotate affected credentials.
- Record the public initial commit SHA in the release notes and SDK release checklist.
- Configure public branch protection, required CI, CODEOWNERS, secret scanning, Dependabot/Renovate, protected release environments, and Trusted Publishing on the public repository before public PyPI beta.

## 27. Offene Fragen

1. Welche exakten Header-Constraints gelten fuer `Idempotency-Key`?
2. Welche safe-ref Felder enthaelt `PublicOperationResult` exakt fuer chat, input wizard und evaluate?
3. Welcher Generator erfuellt nach kurzer Evaluation die Typqualitaets- und Determinismus-Anforderungen am besten?
4. Wer ist Owner fuer PyPI project reservation, public GitHub repo setup, branch protection, CODEOWNERS und Trusted Publishing?
5. Gibt es route-spezifische Pagination Defaults, die vom allgemeinen SDK Default `50` abweichen muessen?

## 28. Beta Readiness Checklist

- Apache-2.0 license and `NOTICE` complete.
- `zenture` import package installed from wheel.
- `py.typed` included.
- Ruff, mypy strict, Pyright pass.
- Coverage gates pass for handwritten code.
- No network in default tests.
- No real tokens in fixtures.
- Redaction regression tests pass.
- Examples run against mocked fixtures.
- OpenAPI artifact locked and drift check passes.
- Generated layer deterministic.
- SDK docs match OpenAPI.
- Token-management routes excluded from API-token SDK surface.
- `POST /v1/evaluate` present in OpenAPI and implemented in SDK.
- `missing_idempotency_key` present in OpenAPI, docs and typed SDK errors.
- Paginator/iterator helpers cover `limit`, `cursor`, `next_cursor`, `created_at desc`, default `50`, max `100`.
- Internal wheel/GitHub Actions artifact produced before public package release.
- Public PyPI beta blocked until SDK reviewer gate passes.
- Public repository is created from a clean reviewed snapshot/orphan initial commit, not from private development history.
- Public GitHub repo under zenture org has branch protection, required CI, CODEOWNERS, secret scanning and dependency automation.
- Trusted Publishing configured.
- Critical review gate completed.
