"""Private HTTP transport lifecycle primitives."""

from __future__ import annotations

from zenture._transport.async_ import AsyncTransport
from zenture._transport.sync import SyncTransport

__all__ = ("AsyncTransport", "SyncTransport")
