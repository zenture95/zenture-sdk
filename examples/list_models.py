"""List public model identifiers available to the current API token."""

from __future__ import annotations

from zenture import Zenture


def main() -> None:
    with Zenture.from_env() as client:
        for mode in ("single", "multi"):
            models = client.models.list(mode=mode)
            print(mode)
            for model in models.models:
                print(model.id, model.display_name)


if __name__ == "__main__":
    main()
