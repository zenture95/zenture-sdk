"""Read billing, usage, and public route limits."""

from __future__ import annotations

from zenture import Zenture


def main() -> None:
    with Zenture.from_env() as client:
        billing = client.billing.get()
        api_usage = client.usage.get(scope="api")
        limits = client.limits.get()

        print(billing.plan, billing.status)
        print(api_usage.operation_count)
        print(limits.operation_statuses)


if __name__ == "__main__":
    main()
