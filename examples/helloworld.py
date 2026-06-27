"""Minimal connectivity check for the zenture SDK."""

from __future__ import annotations

from zenture import Zenture


def main() -> None:
    with Zenture.from_env() as client:
        print(client.helloworld())


if __name__ == "__main__":
    main()
