# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Email provider abstraction and registry.

To add a new provider:
1. Create a ``ProviderDescriptor`` with an ``AuthFlow`` and ``adapter_factory``.
2. Register it in ``PROVIDERS`` (built-in) or via the ``mailpail.providers``
   entry point group (plugin).
3. The GUI and CLI will automatically offer it.

Third-party plugins register via entry points::

    [project.entry-points."mailpail.providers"]
    my-provider = "my_plugin.descriptor:DESCRIPTOR"
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, runtime_checkable

from mailpail.auth import AppPasswordFlow, AuthFlow, Capability, Credential
from mailpail.models import EmailRecord, FilterParams

# ---------------------------------------------------------------------------
# EmailProvider Protocol — the contract every adapter must satisfy
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# AdapterFactory Protocol — callable that produces an EmailProvider
# ---------------------------------------------------------------------------


class AdapterFactory(Protocol):
    """Callable that creates an EmailProvider from a Credential."""

    def __call__(self, credential: Credential) -> EmailProvider: ...


# ---------------------------------------------------------------------------
# ProviderDescriptor — the full description of a provider
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProviderDescriptor:
    """Everything the core needs to know about a provider.

    Built-in providers use the ``ProviderInfo()`` convenience function
    which creates a ProviderDescriptor with IMAP defaults.
    Plugin providers construct this directly.
    """

    key: str
    name: str
    help_url: str
    auth_flow: AuthFlow
    capabilities: Capability
    adapter_factory: AdapterFactory
    # IMAP-specific fields (populated for built-in IMAP providers, empty for API-based)
    server: str = ""
    port: int = 993


# ---------------------------------------------------------------------------
# ProviderInfo — backward-compatible convenience constructor
# ---------------------------------------------------------------------------


def ProviderInfo(
    key: str,
    name: str,
    server: str,
    port: int,
    help_url: str,
) -> ProviderDescriptor:
    """Create a ProviderDescriptor for an IMAP+app-password provider.

    Backward-compatible with the old ``ProviderInfo`` dataclass —
    same positional arguments, same attribute access on the result.
    """
    from mailpail.client import IMAPClient

    def _factory(credential: Credential) -> IMAPClient:
        return IMAPClient(
            username=credential.data["username"],
            password=credential.data["password"],
            server=server,
            port=port,
        )

    return ProviderDescriptor(
        key=key,
        name=name,
        help_url=help_url,
        auth_flow=AppPasswordFlow(provider_key=key, help_url=help_url),
        capabilities=Capability.NONE,
        adapter_factory=_factory,
        server=server,
        port=port,
    )


# ---------------------------------------------------------------------------
# Provider registry — built-in providers
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, ProviderDescriptor] = {
    "aol": ProviderInfo(
        key="aol",
        name="AOL Mail",
        server="export.imap.aol.com",
        port=993,
        help_url="https://login.aol.com/account/security/app-passwords",
    ),
    "gmail": ProviderInfo(
        key="gmail",
        name="Gmail",
        server="imap.gmail.com",
        port=993,
        help_url="https://myaccount.google.com/apppasswords",
    ),
    "outlook": ProviderInfo(
        key="outlook",
        name="Outlook / Hotmail",
        server="outlook.office365.com",
        port=993,
        help_url="https://support.microsoft.com/en-us/account-billing/manage-app-passwords-for-two-step-verification",
    ),
    "yahoo": ProviderInfo(
        key="yahoo",
        name="Yahoo Mail",
        server="imap.mail.yahoo.com",
        port=993,
        help_url="https://help.yahoo.com/kb/generate-manage-third-party-passwords-sln15241.html",
    ),
    "imap": ProviderInfo(
        key="imap",
        name="Other IMAP Server",
        server="",
        port=993,
        help_url="",
    ),
}

DEFAULT_PROVIDER = "aol"


def get_provider_info(key: str = DEFAULT_PROVIDER) -> ProviderDescriptor:
    """Look up a registered provider by key. Raises KeyError if unknown."""
    info = PROVIDERS.get(key)
    if info is None:
        raise KeyError(f"Unknown provider '{key}'. Available: {', '.join(sorted(PROVIDERS))}")
    return info
