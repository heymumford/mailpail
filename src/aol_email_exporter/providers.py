# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Email provider abstraction — AOL is the first adapter.

To add a new provider (Gmail, Outlook, etc.):
1. Create a class satisfying the ``EmailProvider`` Protocol.
2. Register it in ``PROVIDERS``.
3. The GUI and CLI will automatically offer it.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, runtime_checkable

from aol_email_exporter.models import EmailRecord, FilterParams


@runtime_checkable
class EmailProvider(Protocol):
    """Contract that every email service adapter must satisfy."""

    @property
    def display_name(self) -> str: ...

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def list_folders(self) -> list[str]: ...

    def fetch_emails(self, filters: FilterParams) -> list[EmailRecord]: ...

    def __enter__(self) -> EmailProvider: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...


@dataclass(frozen=True)
class ProviderInfo:
    """Registry entry for an email provider."""

    key: str
    name: str
    server: str
    port: int
    help_url: str


# Provider registry — add new services here.
PROVIDERS: dict[str, ProviderInfo] = {
    "aol": ProviderInfo(
        key="aol",
        name="AOL Mail",
        server="export.imap.aol.com",
        port=993,
        help_url="https://login.aol.com/account/security/app-passwords",
    ),
}

DEFAULT_PROVIDER = "aol"


def get_provider_info(key: str = DEFAULT_PROVIDER) -> ProviderInfo:
    """Look up a registered provider by key.  Raises KeyError if unknown."""
    info = PROVIDERS.get(key)
    if info is None:
        raise KeyError(f"Unknown provider '{key}'. Available: {', '.join(sorted(PROVIDERS))}")
    return info
