"""Iterate paginated chat summaries."""

from __future__ import annotations

from zenture import Zenture


def main() -> None:
    with Zenture.from_env() as client:
        for chat in client.chat.iter(limit=50):
            print(chat.chat_id, chat.title)


if __name__ == "__main__":
    main()
