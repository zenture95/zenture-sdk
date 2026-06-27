"""Tests for copy-paste example scripts."""

from __future__ import annotations

import json

from examples.list_models import build_models_payload
from zenture._contract import PublicModelListResponse


class FakeModelsResource:
    def list(self, *, mode: str) -> PublicModelListResponse:
        return PublicModelListResponse.model_validate(
            {
                "models": [
                    {
                        "id": f"{mode}-model",
                        "display_name": f"{mode.title()} Model",
                        "modes": [mode],
                        "capabilities": ["chat"],
                        "is_default": True,
                        "is_available": True,
                        "cost_class": "standard",
                        "provider_display_name": "Example Provider",
                        "max_input_tokens": 8192,
                    }
                ]
            }
        )


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModelsResource()


def test_list_models_example_builds_mode_keyed_json_payload() -> None:
    payload = build_models_payload(FakeClient())

    assert json.loads(json.dumps(payload)) == {
        "single": [
            {
                "id": "single-model",
                "display_name": "Single Model",
                "modes": ["single"],
                "capabilities": ["chat"],
                "is_default": True,
                "is_available": True,
                "cost_class": "standard",
                "provider_display_name": "Example Provider",
                "max_input_tokens": 8192,
            }
        ],
        "multi": [
            {
                "id": "multi-model",
                "display_name": "Multi Model",
                "modes": ["multi"],
                "capabilities": ["chat"],
                "is_default": True,
                "is_available": True,
                "cost_class": "standard",
                "provider_display_name": "Example Provider",
                "max_input_tokens": 8192,
            }
        ],
    }
