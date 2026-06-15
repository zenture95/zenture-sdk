"""OpenAPI contract drift checks for the SDK surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from zenture.idempotency import MAX_IDEMPOTENCY_KEY_LENGTH
from zenture.polling import OperationStatus

OPENAPI_PATH = (
    Path(__file__).resolve().parents[3] / "openapi" / "zenture-public-api-v1.openapi.json"
)


def _load_openapi() -> dict[str, Any]:
    data = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast("dict[str, Any]", data)


def test_openapi_contains_required_sdk_v1_contract() -> None:
    contract = _load_openapi()
    paths = contract["paths"]
    schemas = contract["components"]["schemas"]

    assert "post" in paths["/v1/evaluate"]
    assert "get" in paths["/v1/models"]
    assert "missing_idempotency_key" in schemas["PublicErrorCode"]["enum"]

    chat_request = schemas["ChatRequest"]
    assert chat_request["properties"]["mode"]["default"] == "single"
    assert chat_request["properties"]["mode"]["enum"] == ["single", "multi"]
    assert "agentic" not in chat_request["properties"]["mode"]["enum"]
    assert chat_request["properties"]["models"]["minItems"] == 1
    assert chat_request["properties"]["models"]["maxItems"] == 3
    assert chat_request["properties"]["models"]["uniqueItems"] is True

    models_mode = paths["/v1/models"]["get"]["parameters"][0]["schema"]["enum"]
    assert models_mode == ["single", "multi"]
    assert "agentic" not in models_mode

    operation_result = schemas["PublicOperationResult"]
    assert operation_result["type"] == "object"
    assert operation_result["additionalProperties"] is False
    assert operation_result["required"] == ["result_type"]
    assert set(operation_result["properties"]["result_type"]["enum"]) == {
        "input_wizard",
        "chat",
        "evaluation",
        "unknown",
    }


def test_openapi_api_token_management_routes_are_not_in_sdk_surface() -> None:
    contract = _load_openapi()
    api_token_paths = [path for path in contract["paths"] if path.startswith("/v1/api-tokens")]

    assert api_token_paths
    for path in api_token_paths:
        for operation in contract["paths"][path].values():
            assert operation["x-zenture-auth-mode"] == "user_session"


def test_openapi_operation_statuses_match_sdk_enum() -> None:
    contract = _load_openapi()
    contract_statuses = set(contract["components"]["schemas"]["OperationStatus"]["enum"])
    sdk_statuses = {status.value for status in OperationStatus}

    assert contract_statuses == sdk_statuses

    result_status = contract["components"]["schemas"]["PublicOperationResult"]["properties"][
        "status"
    ]
    assert {"$ref": "#/components/schemas/OperationStatus"} in result_status["anyOf"]


def test_openapi_idempotency_key_max_length_matches_sdk_limit() -> None:
    contract = _load_openapi()
    paths = contract["paths"]
    assert isinstance(paths, dict)
    typed_paths = cast("dict[str, Any]", paths)
    required_limits: set[int] = set()

    for path_item in typed_paths.values():
        assert isinstance(path_item, dict)
        typed_path_item = cast("dict[str, Any]", path_item)
        for operation in typed_path_item.values():
            assert isinstance(operation, dict)
            typed_operation = cast("dict[str, Any]", operation)
            if typed_operation.get("x-zenture-idempotency-required") is not True:
                continue

            parameters = typed_operation["parameters"]
            assert isinstance(parameters, list)
            typed_parameters = cast("list[object]", parameters)
            idempotency_parameters: list[dict[str, Any]] = []
            for parameter in typed_parameters:
                if not isinstance(parameter, dict):
                    continue
                typed_parameter = cast("dict[str, Any]", parameter)
                if typed_parameter.get("name") == "Idempotency-Key":
                    idempotency_parameters.append(typed_parameter)

            assert len(idempotency_parameters) == 1
            idempotency_parameter = idempotency_parameters[0]
            schema = idempotency_parameter["schema"]
            assert isinstance(schema, dict)
            typed_schema = cast("dict[str, Any]", schema)
            assert typed_schema["minLength"] == 1
            required_limits.add(cast("int", typed_schema["maxLength"]))

    assert required_limits == {MAX_IDEMPOTENCY_KEY_LENGTH}
