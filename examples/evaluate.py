"""Run an evaluation operation."""

from __future__ import annotations

from zenture import Zenture
from zenture.idempotency import idempotency_key


def main() -> None:
    key = idempotency_key("example", "evaluation", "v1")
    with Zenture.from_env() as client:
        result = client.evaluations.run(
            user_message="What does the SDK do?",
            ai_answer="It helps server-side Python integrations call zenture.",
            idempotency_key=key,
            timeout=120.0,
        )
        print(result.operation_id, result.status)


if __name__ == "__main__":
    main()
