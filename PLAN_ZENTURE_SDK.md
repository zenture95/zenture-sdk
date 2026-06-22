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

Aktueller SDK-Plan Status:

- Phase 0A Repository Governance Bootstrap: lokal umgesetzt und remote teilweise konfiguriert. GitHub Issues, merge settings, Actions read-only permissions, `pypi`/`testpypi` environments, Dependabot vulnerability alerts und automated security fixes sind eingerichtet. Branch Protection, secret scanning, push protection und protected environment reviewers sind auf dem aktuellen privaten GitHub-Plan blockiert und bleiben Go-Live-Gates.
- Phase 1 Repo Foundation: umgesetzt. Das Repo hat moderne Python-Package-Metadaten, `src/zenture`, `py.typed`, Ruff, mypy strict, Pyright, pytest, build/twine CI, release workflow und Governance-Dokumente.
- Phase 2 Core Runtime: umgesetzt und lokal verifiziert. Vorhanden sind strict Pydantic-basierte Core Models, redaction helpers, typed errors, idempotency helpers, rate-limit header parsing, `ZentureConfig`, retry policy, polling basics und sync/async httpx transport lifecycle mit Tests.
- Security issue intake: GitHub Issues sind als erlaubter Bootstrap-Meldeweg dokumentiert; ein Security-Issue-Template ist lokal vorhanden.
- Phase-2-Verifikation: Ruff format/check, mypy strict, Pyright, pytest, Coverage, sdist/wheel build und Twine metadata check sind lokal gruen. Coverage liegt aktuell ueber dem `90%` Gate.
- Phase 3 Contract/Model Layer: abgeschlossen. Das aktuelle OpenAPI-Artefakt ist lokal unter `openapi/zenture-public-api-v1.openapi.json` gespiegelt und im sdist enthalten; `zenture._contract` enthaelt die interne minimale Contract-Schicht fuer Operationen, Errors, Requests, Read Responses und Rate-Limit Header. Contract-Drift-Tests pruefen `POST /v1/evaluate`, `missing_idempotency_key`, bounded `PublicOperationResult`, Request-Required-Felder, Phase-4-Response-Required-Felder, `Idempotency-Key` min/max Constraints, API-token Management Exclusion und Operation Status Alignment.
- Phase 4 Resource Clients: abgeschlossen gegen den aktuell lokal gespiegelten OpenAPI-Contract. `Zenture`/`AsyncZenture`, private sync/async Transport Request-Helpers, `helloworld`, `operations`, `chat`, `models`, `input_wizard`, `evaluations`, `billing`, `usage` und `limits` sind implementiert und mit `httpx.MockTransport` getestet. `helloworld` sendet gemaess OpenAPI `x-zenture-auth-mode: none` keine Authorization Header; mutierende Routes senden validierte `Idempotency-Key` Header. SDK-owned sync/async HTTP Clients nutzen explizite Timeout-Defaults und die Request-Pfade verdrahten Retry-Entscheidungen inklusive `Retry-After`, Backoff und "kein Retry fuer mutierende Requests ohne Idempotency-Key".
- Phase-4-Patch Model Discovery und Single-/Multi-Model Chat: umgesetzt. `GET /v1/models` ist lokal gespiegelt, `PublicModel`/`PublicModelListResponse` und `ModelMode` sind in der internen Contract-Schicht vorhanden, `client.models.list(mode=None|"single"|"multi")` ist sync/async implementiert, Chat validiert `mode`, `model` und `models` SDK-seitig, und Agentic Chat bleibt in V1 bewusst nicht public.
- Phase 5 Operation-Polling und Pagination sind umgesetzt:
  `operations.wait(...)` existiert sync/async, `chat.run(...)` nutzt den
  generischen Wait-Pfad, und `input_wizard.run(...)` sowie
  `evaluations.run(...)` sind sync/async vorhanden. Nach dem Gateway/OpenAPI
  Pagination-Update unterstuetzen `chat.list(...)`,
  `chat.messages(...)` und `evaluations.list(...)` `limit`/`cursor`; sync/async
  Iteratoren laufen bis `next_cursor is None`.

Relevante Plattformquellen:

- `zenture-api-gateway/docs/PLAN_PUBLIC_API_GATEWAY.md`
- `zenture-api-gateway/docs/SDK_AND_DEVELOPER_EXPERIENCE.md`
- `zenture-api-gateway/openapi/zenture-public-api-v1.openapi.json`
- Public docs unter `zenture-api-gateway/docs/public/`

OpenAPI Stand:

- OpenAPI: `3.1.0`
- Contract Version: `1.0.0-rc.2`
- Public server:
  - `https://api.zenture.app`
- Public API Base Path: `/v1`

V1 API-token Routen im aktuellen OpenAPI-Artefakt:

- `GET /v1/helloworld`
- `POST /v1/chat`
- `POST /v1/input-wizard`
- `POST /v1/evaluate`
- `GET /v1/models`
- `GET /v1/operations/{operation_id}`
- `GET /v1/chats`
- `GET /v1/chats/{chat_id}`
- `GET /v1/chats/{chat_id}/messages`
- `GET /v1/evaluations`
- `GET /v1/evaluations/{evaluation_id}`
- `GET /v1/billing`
- `GET /v1/usage`
- `GET /v1/limits`

Aktueller Contract Checkpoint:

- `POST /v1/evaluate` ist im lokal gespiegelten OpenAPI-Artefakt vorhanden.
- `missing_idempotency_key` ist im `PublicErrorCode` Enum vorhanden.
- `PublicOperationResult` ist bounded (`additionalProperties: false`) und safe-ref-first typisiert.
- `GET /v1/models`, `PublicModel`, `PublicModelListResponse` und die ChatRequest-Felder `mode`, `model`, `models` sind im lokal gespiegelten OpenAPI-Artefakt vorhanden.
- `mode` ist in V1 auf `single` und `multi` begrenzt; `agentic` ist kein public SDK-Modus.
- API-token Management Routen bleiben im OpenAPI-Artefakt enthalten, sind aber `user_session` Routen und werden nicht Teil der API-token SDK Surface.
- SDK Resource Clients werden erst nach gruenem Contract-Drift-Test und Generator-/Modellstrategie implementiert; dieser Check ist fuer Phase 4 und den Model-Discovery-Patch gruen.

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
│       ├── _contract/
│       │   ├── __init__.py
│       │   ├── headers.py
│       │   └── models.py
│       └── _generated/
│           ├── __init__.py
│           └── ...  # optional future generated code only
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
│   │   └── contract/
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
from zenture import Zenture

client = Zenture.from_env()

message = client.helloworld()
print(message)
```

Context-manager usage:

```python
from zenture import Zenture

with Zenture.from_env() as client:
    result = client.input_wizard.run(
        prompt="Draft a concise onboarding prompt for a support chatbot.",
        idempotency_key="ticket-428-input-wizard-v1",
    )
```

Async usage:

```python
from zenture import AsyncZenture

async with AsyncZenture.from_env() as client:
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
)

latest = client.operations.get(operation.operation_id)
print(latest.status)
```

Model discovery:

```python
from zenture import Zenture

client = Zenture.from_env()

single_models = client.models.list(mode="single")
multi_models = client.models.list(mode="multi")

print(single_models.models[0].id)
print(multi_models.models[0].display_name)
```

Single-/Multi-Model Chat:

```python
from zenture import Zenture

client = Zenture.from_env()

single = client.chat.run(
    message="Summarize this support transcript.",
    mode="single",
    model="public-model-a",
    idempotency_key="case-123-chat-single-001",
    timeout=120.0,
)

multi = client.chat.run(
    message="Compare these candidate answers.",
    mode="multi",
    models=["public-model-a", "public-model-b"],
    idempotency_key="case-123-chat-multi-001",
    timeout=120.0,
)

print(single.operation_id)
print(multi.status)
```

Rules:

- `mode="single"` is the default, accepts optional `model`, and rejects
  `models`.
- `mode="multi"` requires 1 to 3 unique `models` and rejects `model`.
- `agentic` is not a public V1 mode and must be rejected client-side.
- The server remains the authority for model availability, plan, billing and
  permission checks.

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

Evaluation create/run is V1-pflichtig and is present in the locally mirrored OpenAPI contract. SDK implementation belongs to Phase 4 after Phase 3 model/generator strategy is locked:

```python
result = client.evaluations.run(
    user_message="What is SOC 2?",
    ai_answer="SOC 2 is a compliance framework...",
    idempotency_key="case-123-eval-001",
    timeout=120.0,
)
```

SDK Beta must include evaluation create/run because the route is now part of the V1 SDK contract.

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

Contract-derived:

- OpenAPI Artefakt wird in `openapi/zenture-public-api-v1.openapi.json` im SDK Repo gespiegelt.
- Contract Code lebt unter `zenture._contract`.
- Contract Code ist intern und wird nicht als primäre API dokumentiert.
- Contract Drift wird deterministisch in CI gegen das lokale OpenAPI-Artefakt geprueft.
- Generated Code unter `zenture._generated` bleibt eine optionale spaetere Erweiterung, falls ein Generator klare Vorteile liefert.
- Contract Typen muessen Pydantic v2, `strict=True`, `extra="forbid"` und klare Typen/Enums nutzen.

Handwritten:

- `Zenture`, `AsyncZenture`, Resources, Polling, Errors, Redaction, Retry und Idempotency bleiben handgeschrieben.
- Public API Namen sollen produktnah sein, nicht operationId-nah.
- Der handwritten Layer glättet Gateway-Details, ohne Contract-Semantik zu verstecken.

Tooling-Entscheidung fuer Phase 3:

- Kandidaten pruefen: `openapi-python-client`, `datamodel-code-generator`, eigener minimaler Generator fuer Pydantic Models.
- Entscheidungskriterium: Typqualitaet, Pydantic v2 Support, deterministische Diffs, geringe Dependency-Last, gute Kontrolle ueber Public API.
- Wenn Generator-Output zu gross oder instabil ist, nur Pydantic Models generieren und Transport handschreiben.

Generator-Evaluation:

| Option | Vorteil | Risiko | Vorlaeufige Bewertung |
| --- | --- | --- | --- |
| `openapi-python-client` | Vollstaendiger Client aus OpenAPI, schnelle Abdeckung vieler Operationen | Zu viel Operation-/Client-Surface fuer Phase 3; Generator-Output wuerde Public-API-Review erschweren; Sync/Async Ergonomie bleibt trotzdem handzuschneiden | Nicht fuer Phase 3 verwenden |
| `datamodel-code-generator` | Gut fuer contract-derived Pydantic Models, Transport bleibt kontrolliert handgeschrieben | Fuer die aktuell benoetigten Schemas mehr Tooling als Nutzen; Output-Style und Diff-Stabilitaet muessten separat gepinnt und reviewed werden | Zurueckstellen, bis Contract-Breite groesser wird |
| Eigener minimaler contract-derived Layer | Maximale Kontrolle, minimale Public Surface, exakt auf zenture V1 Kernschemas zugeschnitten, keine neue Generator-Dependency | Manuelle Pflege erfordert Drift-Tests gegen OpenAPI | Gewaehlt fuer Phase 3 |

Phase-3-Entscheidung: eigener minimaler interner `zenture._contract` Layer. Begruendung: Die aktuell benoetigten V1-Kernschemas sind klein, bounded und sicherheitsrelevant; Reviewbarkeit, strikte Typisierung, kleine Module und geringe Public Surface sind wichtiger als ein vollstaendiger generierter Client. Generatoren bleiben spaetere Optionen, wenn mehr Contract-Abdeckung gebraucht wird und ein reproduzierbarer Output-Gate etabliert ist.

Implementierter Phase-3-Contract-Layer:

- `zenture._contract.models`
  - `OperationStatus`
  - `PublicErrorCode`
  - `PublicError`
  - `PublicErrorEnvelope`
  - `PublicOperationError`
  - `PublicOperationResult`
  - `PublicOperationResponse`
  - `ChatRequest`
  - `InputWizardRequest`
  - `EvaluateRequest`
- `zenture._contract.headers`
  - `RATE_LIMIT_HEADER_NAMES`
  - interne Re-Exports fuer `RateLimitInfo` und `parse_rate_limit_headers`
- Keine Exports aus `zenture.__init__`.
- Keine API-token Management Models oder Resource Surface.
- Response Models validieren API-JSON-kompatible Enum-Strings fuer bounded Contract Enums und bleiben ansonsten strict.
- `PublicOperationResult.completed_at` wird als timezone-aware datetime validiert.
- Operation-Fehler sind bewusst von Gateway-Error-Envelopes getrennt:
  `PublicOperationError.code` ist ein bounded string fuer domain-spezifische
  terminale Operation-Codes wie `chat_execution_failed`; HTTP/Gateway-Errors
  bleiben ueber `PublicErrorCode` und SDK-Exceptions modelliert.
- Drift-Tests vergleichen Enums, required fields, bounded result shape, Rate-Limit Header und API-token Management Exclusion gegen das lokale OpenAPI-Artefakt.

## 10. Pydantic Models Und Typing

Pydantic v2 ist Pflicht fuer Request/Response Models.

Model-Regeln:

- `model_config = ConfigDict(extra="forbid", frozen=True, strict=True)` fuer public response/value models und interne Contract Models, soweit sinnvoll.
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
- `missing_idempotency_key`
- `dependency_unavailable`
- `capacity_unavailable`
- `internal_error`
- `idempotency_conflict`
- `operation_expired`

Error-Code Entscheidung:

- Fehlender `Idempotency-Key` nutzt den stabilen Error Code `missing_idempotency_key` mit HTTP `400`.
- `validation_failed` bleibt fuer sonstige Body-, Path-, Query- und Header-Validation.
- OpenAPI, Gateway, Docs und SDK muessen diesen Error Code konsistent enthalten; der SDK-Contract-Test sichert das OpenAPI-Alignment lokal ab.

## 11. HTTPX Nutzung

`httpx` ist der einzige HTTP Transport.

Client Optionen:

```python
Zenture(
    api_key: str,
    base_url: str | None = None,
    http_client: httpx.Client | None = None,
    user_agent: str | None = None,
    connect_timeout: float | None = None,
    read_timeout: float | None = None,
    write_timeout: float | None = None,
    pool_timeout: float | None = None,
    max_retries: int | None = None,
    initial_retry_backoff: float | None = None,
    max_retry_backoff: float | None = None,
)
```

Defaults:

- `base_url`: `https://api.zenture.app`
- `timeout`: connect `5s`, read/write/pool `30s`; long operation waiting uses polling timeout, not HTTP read timeout.
- `max_retries`: `2`
- `initial_retry_backoff`: `0.5s`
- `max_retry_backoff`: `8s`
- `User-Agent`: `zenture-sdk-python/{sdk_version}` by default, overrideable by caller-owned server integrations.
- Headers:
  - `Authorization: Bearer <api_key>`
  - `Content-Type: application/json` for JSON requests
  - `Idempotency-Key` only when required/provided

Rules:

- No API key in URL.
- No automatic environment lookup except `Zenture.from_env()`.
- `from_env()` reads `ZENTURE_API_KEY`.
- Public docs should prefer `Zenture.from_env()` / `AsyncZenture.from_env()`
  over examples that pass token material directly to Python constructors.
- Caller-provided `httpx.Client` / `httpx.AsyncClient` instances are accepted for
  advanced integrations and tests. The caller remains responsible for their
  timeout, limits and lifecycle policy.
- `ZENTURE_BASE_URL` is supported only for approved non-production and local debugging usage with test tokens. Public docs must state that base URLs must never come from user input and must not publish non-production API hostnames.
- Base URL validation allows only:
  - `https://api.zenture.app` for live tokens
  - approved non-production zenture API origins for test tokens
  - local debugging origins on `localhost`, `127.0.0.1`, or `::1` for test tokens
- Base URL validation rejects arbitrary HTTPS origins such as `https://evil.example`, URL credentials, paths, query strings and fragments.
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
- `error_from_response(...)` uses the explicitly named forward-compatible `ForwardCompatibleErrorEnvelope`, not the strict `_contract.PublicErrorEnvelope`, so future public error codes remain observable without widening the internal contract model.
- There must not be two same-named SDK models with different error-envelope semantics.

## 13. Polling Helpers Fuer Async Operations

High-level `.run()` helpers:

- Create operation.
- Poll until terminal status.
- Return a typed `OperationRunResult`, never a naked domain answer.
- Auto-generate an idempotency key only when the method is explicitly high-level and exposes generated metadata.
- Include at least `operation_id`, `status`, `result`, `error`,
  `idempotency_key`, and optional `request_id`/`last_request_id`.
- If create succeeds but local polling later times out or is stopped, raise a
  polling exception with safe recovery attributes `operation_id`,
  `idempotency_key`, and optional `last_request_id`. These attributes are for
  explicit caller recovery and must not be interpolated into exception
  `str()`/`repr()`.
- Recovery path: call `operations.get(operation_id)` or retry with the same
  `idempotency_key`. Do not retry a billable mutation with a newly generated key
  after local polling failure.

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
- Phase 5 uses deterministic bounded interval progression for testability:
  double the current interval until `max_interval`, with no jitter.
- Timeout: caller-provided; recommended examples use `120s`.
- Stop on terminal statuses: `succeeded`, `failed`, `cancelled`, `expired`.
- `Retry-After` handling remains in the existing HTTP transport retry path.
  Phase 5 does not add a separate polling-header wait layer.
- Treat 429 during polling as retryable only through the existing transport
  retry policy.
- Treat `operation_expired` as terminal non-retryable.

Cancellation:

- Sync polling accepts a `stop: Callable[[], bool] | None`.
- Async polling propagates `asyncio.CancelledError` from task cancellation and
  accepts the same optional local stop callable.
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

- Validate key length against OpenAPI: `minLength=1`, `maxLength=255`.
- Keep the SDK safe-character policy intentionally narrower than OpenAPI for ergonomics and secret/PII avoidance; document this as SDK-side safety policy, not gateway contract.
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

- List methods accept `limit: int = 50` and `cursor: str | None = None`.
- List methods return typed page objects with resource-specific item fields
  and `next_cursor`.
- Resource clients expose sync and async iterator helpers:
  - `client.chat.iter(limit=50, cursor=None)`
  - `client.chat.iter_messages(chat_id, limit=50, cursor=None)`
  - `client.evaluations.iter(limit=50, cursor=None)`
  - `async for chat in client.chat.iter(limit=50): ...`
- Iterators must be lazy and stop when `next_cursor` is absent.
- Iterators must not hide API errors or rate limits.
- Tests must cover page boundaries, empty pages, max-limit validation, and cursor propagation.

Current checkpoint:

- The locally mirrored OpenAPI artifact exposes `limit` and `cursor` query
  parameters on `GET /v1/chats`, `GET /v1/chats/{chat_id}/messages` and
  `GET /v1/evaluations`, plus nullable `next_cursor` responses.
- Phase 5 implements typed paginated reads and iterator helpers sync/async.

## 16. Retry, Timeout Und Backoff Policy

Retryable by default:

- Retryable HTTP error responses for safe methods.
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

- Deterministic exponential backoff.
- Cap per-attempt sleep.
- Respect server `Retry-After` over client guess.
- Expose retry metadata only in debug-safe form.

Timeouts:

- SDK-owned HTTP clients use explicit defaults: connect `5s`,
  read/write/pool `30s`.
- Callers may override individual timeout values on `Zenture` and
  `AsyncZenture`.
- HTTP request timeout is separate from operation polling timeout.
- `run(timeout=...)` means total operation wait budget, not raw HTTP read timeout.
- Create request may pass `wait=false` or `wait=0` for immediate async behavior when supported by contract.

Current implementation checkpoint:

- Sync and async `_request(...)` paths apply the shared retry decision policy.
- `Retry-After` is honored before deterministic exponential backoff.
- Mutating requests are not retried unless an `Idempotency-Key` is present.
- `missing_idempotency_key` and other non-retryable public error codes are not
  retried.
- Client-side `httpx.HTTPError` network exceptions are mapped to
  `ZentureTransportError` and are not retried yet; adding network-exception
  retry classification is a separate Phase-5 decision.

## 17. Redaction Und Secret Handling

Non-negotiable:

- API token never appears in logs, exceptions, repr, test snapshots or debug output.
- Authorization header is always redacted as `<redacted>`.
- Request/response bodies are not logged by default.
- Prompt and model-answer text are considered sensitive content.
- Billing/payment payloads are considered sensitive.
- Examples load tokens from env vars only.
- Public examples must not hardcode token-like strings in Python files. Local
  `.env` files are acceptable only when uncommitted and loaded into the process
  environment before creating the SDK client.
- Fixtures use synthetic non-secret placeholders only; tests must never use real
  token prefixes with realistic entropy.

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

- Located under `tests/unit/`.
- Error mapping per public error code.
- Rate-limit header parsing.
- Retry decision matrix.
- Idempotency key validation/generation.
- Redaction helpers.
- Pydantic model validation.
- Base URL and config validation.
- Sync/async close semantics.

Mocked HTTP integration tests:

- Located under `tests/integration/`; contract drift tests live under
  `tests/integration/contract/`.
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
- `POST /v1/evaluate` is present in the committed OpenAPI artifact.
- `missing_idempotency_key` is present in the committed OpenAPI artifact and maps to the typed SDK error.
- `PublicOperationResult` remains bounded and safe-ref-first.
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
  - Python `3.11`, `3.12` and `3.13`
  - Ruff format check
  - Ruff lint
  - Mypy strict
  - Pyright
  - Pytest through `coverage run`
  - Coverage report enforcing `fail_under = 90`
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

- Internal prerelease versions: `0.1.0aN`, `0.1.0bN` or `0.1.0rcN`.
- Current local package version checkpoint: `0.1.0b1`.
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
- Evaluation create/run

Evaluation create example is mandatory for SDK Beta.

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

- Verify `POST /v1/evaluate` is present in the committed OpenAPI contract.
- Verify final OpenAPI error code catalog includes `missing_idempotency_key`.
- Verify bounded safe-ref-first `PublicOperationResult`.
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
- Implement sync/async transport with httpx lifecycle primitives.
- Add unit tests for all core policies.
- Current status: complete. The core runtime is intentionally limited to reusable SDK primitives; public `Zenture`/`AsyncZenture` clients and resource methods start after Phase 3 contract/model work.

Phase 3: Models and generated layer

- Copy locked OpenAPI artifact into `openapi/`.
- Select generator.
- Generate or handcraft Pydantic model baseline.
- Add regeneration and contract drift checks.
- Current status: complete for the Phase-3 baseline. The selected strategy is a minimal handwritten/contract-derived `zenture._contract` layer with OpenAPI drift tests; no full generated client is introduced.

Phase 4: Resource clients

- Implement `helloworld`.
- Implement `operations`.
- Implement `chat`.
- Implement `input_wizard`.
- Implement evaluation create.
- Implement read resources: chats, evaluations, billing, usage, limits.
- Exclude API-token management routes.
- Wire transport request paths to the shared retry, timeout and idempotency
  safety policies.
- Current status: complete against the current OpenAPI artifact. Public clients expose `operations`, `chat`, `models`, `input_wizard`, `evaluations`, `billing`, `usage`, `limits` and `helloworld`; API-token management routes remain excluded. Runtime implementation packages are private (`zenture._transport`, `zenture._resources`) to avoid accidental public API expansion. SDK-owned HTTP clients now use explicit timeout defaults, and sync/async request paths retry only retryable HTTP responses under the shared policy.

Phase 5: Polling, retries, pagination and idempotent run helpers

- Extend `.run()` helpers beyond `chat.run(...)` where product UX requires it.
- Implement generic operation wait semantics.
- Current status: complete for generic operation waiting and run-helper
  unification. `operations.wait(...)` returns the terminal
  `PublicOperationResponse`; timeout and local stop raise redacted SDK
  exceptions; async task cancellation propagates.
- Implemented run helpers: `chat.run(...)`, `input_wizard.run(...)`,
  `evaluations.run(...)`, sync and async.
- Implemented pagination helpers after OpenAPI exposed `limit` and `cursor`:
  `chat.list(limit=50, cursor=None)`, `chat.messages(...)`,
  `evaluations.list(...)`, `chat.iter(...)`, `chat.iter_messages(...)`, and
  `evaluations.iter(...)`, sync and async.
- Design decision: deterministic polling intervals only; jitter is deferred.
- Deferred: separate polling-layer `Retry-After`/rate-limit scheduling and
  client-side network exception retry classification. Existing transport
  retry behavior remains the only retry layer.
- Added timeout, cancellation, failed-operation, cancelled/expired terminal,
  interval progression and idempotency-safety tests.

Phase 6: Docs, examples and public README

- Current status: complete for public beta documentation scope.
- README is beta-oriented and public-safe: install, package/import names,
  supported Python versions, server-side token warning, webapp token creation,
  env setup, sync/async quickstarts, model discovery, chat, input wizard,
  evaluations, operation polling, idempotency, errors, retry/rate-limit policy,
  base URL policy, local verification, security disclosure, and license.
- Public docs exist under `docs/` for authentication, idempotency,
  async operations, errors, rate limits, security, API overview, and release.
- Executable examples exist under `examples/` and use `Zenture.from_env()` or
  `AsyncZenture.from_env()` with no token literals.
- Docs/examples hygiene tests verify public-safe content, compile examples, and
  prevent forbidden token, base URL, and private-path patterns.
- Pagination documentation and examples cover `limit`, `cursor`, `next_cursor`
  and iterator helpers.

Phase 6B: Human and agent onboarding documentation

This phase runs after SDK core logic and docs/examples work, but before the
critical review gate and INT/prerelease testing. The goal is to make the
repository self-explanatory for external developers and future coding agents
without relying on private planning context.

- Update `README.md` as the human entrypoint:
  - explain what `zenture-sdk` is and is not;
  - show install, configuration, sync and async quickstarts;
  - document the resource layout, operation polling model, idempotency, typed errors, retries, pagination, and rate-limit handling;
  - explain base URL behavior: production default, INT/local only for controlled debugging;
  - link to public API docs and public support/security channels;
  - clearly state that API-token management routes are not part of the SDK surface.
- Add root `AGENTS.md` as the agent entrypoint:
  - summarize repository purpose, package/import names, architecture, module map, and public vs internal surfaces;
  - name OpenAPI as the contract source of truth and explain the `_contract` drift-test strategy;
  - list required local commands for formatting, linting, typing, tests, coverage, build, twine check, and secret scans;
  - document security red lines: never log tokens, never persist plaintext API keys, never expose internal gateway/backend paths, never add arbitrary base URL origins, and never export internal `_contract` names from the top-level package;
  - define contribution expectations for new resources, models, examples, docs, and tests.
- Keep both files public-safe:
  - no private repository paths;
  - no private deployment details;
  - no credentials, tokens, internal customer data, raw payloads, or private planning notes;
  - no instructions that require access to zenture private infrastructure.
- Add or update lightweight docs tests/grep checks proving:
  - `README.md` covers install, quickstart, sync, async, polling, idempotency, errors, retries, rate limits, and security;
  - `AGENTS.md` covers architecture, module map, commands, contract drift, and security red lines;
  - neither file mentions private paths, `.env` secrets, internal gateway/backend URLs, or fake real-looking live tokens.
- Current status: complete. Root `AGENTS.md` is public-safe and documents repo
  purpose, package/import names, architecture map, public versus internal
  surface, OpenAPI contract drift, required commands, security red lines, and
  contribution expectations.

Phase 7: Critical review gate

- Run review using criteria above.
- Fix all prerelease blockers.
- Verify static quality, package build and no-network tests.

Phase 8: Prerelease Readiness / Pre-Go-Live Config

- Start only after Phase 6B onboarding documentation and Phase 7 critical
  review gate are complete.
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

Phase 10: Final public go-live safety gate

This is the last mandatory gate before switching the repository to public visibility or publishing a public PyPI beta/stable release. It must be executed from the clean public snapshot/orphan history created in Phase 9, not from the private development history.

- Confirm repository visibility is still private before the checklist starts.
- Confirm the default branch points to the clean public initial commit/history.
- Confirm no private branches, stale release branches, experimental branches, or private tags remain on the remote.
- Confirm `git log --all --stat` and repository file listing contain no private planning churn, local artifacts, `.env` files, credentials, customer data, raw API payloads, private OpenAPI drafts, or generated temp files.
- Run a final secret scan on the exact tree that will become public.
- Run the full public CI on the clean public branch: Ruff, mypy strict, Pyright, pytest, coverage, examples, OpenAPI drift checks, build, and `twine check`.
- Enable branch protection or rulesets on `main` before accepting external work.
- Require pull requests before merge.
- Require CODEOWNERS review.
- Require required status checks for governance, Python versions, package build, docs/examples, and contract drift.
- Dismiss stale approvals.
- Require conversation resolution.
- Require linear history.
- Block force pushes and branch deletion.
- Apply branch protection to administrators where the GitHub plan supports it.
- Enable secret scanning and push protection before changing visibility to public.
- Enable Dependabot alerts, Dependabot security updates, and Dependabot/Renovate dependency PRs.
- Disable unused repository features such as wiki/projects unless intentionally needed.
- Confirm Issues are enabled and issue templates warn against posting secrets, customer data, or exploit instructions.
- Confirm `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `NOTICE`, `LICENSE`, `CHANGELOG.md`, `README.md`, `AGENTS.md`, docs, and examples are public-safe.
- Confirm GitHub Actions default token permissions are read-only.
- Confirm release workflows grant `id-token: write` only for publishing jobs.
- Confirm `pypi` and `testpypi` environments exist; `pypi` requires manual approval/reviewer where the GitHub plan supports it.
- Configure PyPI Trusted Publishing against the final repository owner/name, workflow file, and `pypi` environment.
- Verify PyPI project name `zenture-sdk` is still available or already controlled by zenture.
- Publish only from a protected version tag.
- Verify the built wheel/sdist install cleanly in a fresh virtual environment.
- Verify README renders correctly on PyPI/TestPyPI before stable release.
- Switch repository visibility to public only after all previous items pass.
- After visibility switch, re-check branch protection, secret scanning, CODEOWNERS, Actions permissions, environments, and Dependabot settings because availability may change between private and public visibility.
- Create the GitHub Release only after the public repository settings are verified.
- Publish public PyPI beta/stable only after the public repository settings and release artifact checks are verified.
- Record final go-live evidence: public initial commit SHA, OpenAPI contract version, SDK version, CI run URL, package artifact hashes, PyPI release URL, and reviewer approval.

## 27. Offene Fragen

1. Soll die SDK Safe-Character-Policy fuer `Idempotency-Key` langfristig exakt
   im OpenAPI Contract formalisiert werden? Aktueller Stand: OpenAPI beschreibt
   Bounds und eine SDK-safe Policy in Textform; ein striktes Pattern bleibt
   offen fuer eine spaetere Gateway-Kompatibilitaetsentscheidung.
2. Wird `PublicOperationResult` in Phase 3 als ein gemeinsames bounded Model
   modelliert oder zusaetzlich durch route-spezifische Convenience-Wrappers
   ergaenzt? Aktueller Stand: gemeinsames bounded Model ist fuer V1 beta
   umgesetzt; Convenience-Wrappers bleiben post-beta optional.
3. Welcher Generator erfuellt nach kurzer Evaluation die Typqualitaets- und
   Determinismus-Anforderungen am besten? Erledigt fuer V1 beta: kein voller
   generierter Client; minimaler interner `_contract` Layer plus OpenAPI
   Drift-Tests.
4. Wer ist Owner fuer PyPI project reservation, public GitHub repo setup,
   branch protection, CODEOWNERS und Trusted Publishing? Offen und Phase-8/9
   Release-Governance-Blocker.
5. Gibt es route-spezifische Pagination Defaults, die vom allgemeinen SDK
   Default `50` abweichen muessen? Erledigt fuer V1 beta: Gateway/OpenAPI und
   SDK nutzen default `50`, min `1`, max `100` fuer Chats, Chat-Messages und
   Evaluations.

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
- Phase 10 final public go-live safety gate completed with recorded evidence.
- Critical review gate completed.
