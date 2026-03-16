# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Auth flow abstraction — decouples credential acquisition from email sessions.

The core ships ``AppPasswordFlow`` (username + password form).
Plugin packages provide their own flows (OAuth PKCE, MSAL, device-code, etc.).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Protocol

# ---------------------------------------------------------------------------
# Capability flags — what an adapter actually supports
# ---------------------------------------------------------------------------


class Capability(enum.Flag):
    """What an email provider adapter supports.

    Use bitwise OR to combine: ``Capability.SEARCH | Capability.ATTACHMENTS``
    """

    NONE = 0
    SEARCH = enum.auto()  # server-side keyword search beyond basic IMAP criteria
    ATTACHMENTS = enum.auto()  # can fetch attachment bytes (not just has_attachments flag)
    LABELS = enum.auto()  # provider uses labels/tags instead of folders (Gmail)
    DELEGATED = enum.auto()  # shared mailbox / delegated access supported
    INCREMENTAL = enum.auto()  # supports IMAP IDLE or push for incremental fetch


# ---------------------------------------------------------------------------
# Credential — opaque bundle passed to an adapter's connect()
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Credential:
    """Opaque credential bundle produced by an AuthFlow.

    The adapter receiving this knows what fields are in ``data``;
    nothing else needs to.
    """

    provider_key: str
    data: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# FormField — drives dynamic GUI form rendering
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FormField:
    """Descriptor for a single input field the GUI must render."""

    key: str  # maps to the key in form_values dict
    label: str  # user-visible label
    placeholder: str  # hint text
    secret: bool = False  # True → render as password field
    required: bool = True


# ---------------------------------------------------------------------------
# AuthFlow Protocol — the contract plugin auth flows must satisfy
# ---------------------------------------------------------------------------


class AuthFlow(Protocol):
    """Contract for acquiring credentials — decoupled from the email session.

    Implementations live in the core (AppPasswordFlow) or in plugin packages
    (e.g., OAuthPKCEFlow in mailpail-gmail-oauth).
    """

    @property
    def requires_browser(self) -> bool:
        """True if the flow needs a browser redirect (OAuth, MSAL, etc.)."""
        ...

    def form_fields(self) -> list[FormField]:
        """Fields the GUI must render. Empty for browser-redirect flows."""
        ...

    def acquire(self, form_values: dict[str, str]) -> Credential:
        """Blocking call that returns a Credential or raises AuthError.

        For browser flows: opens browser, starts callback server, blocks
        until redirect completes, returns token bundle.
        For password flows: wraps form values into a Credential.
        """
        ...

    def refresh(self, credential: Credential) -> Credential:
        """Return a refreshed Credential. No-op for non-expiring credentials."""
        ...


class AuthError(Exception):
    """Raised when credential acquisition fails."""


# ---------------------------------------------------------------------------
# AppPasswordFlow — the built-in flow for username + app-password providers
# ---------------------------------------------------------------------------


class AppPasswordFlow:
    """Username + app-password auth flow. Ships with core."""

    def __init__(self, provider_key: str = "", help_url: str = "") -> None:
        self._provider_key = provider_key
        self._help_url = help_url

    @property
    def requires_browser(self) -> bool:
        return False

    def form_fields(self) -> list[FormField]:
        return [
            FormField(key="username", label="Email Address", placeholder="your.email@example.com"),
            FormField(key="password", label="App Password", placeholder="App Password", secret=True),
        ]

    def acquire(self, form_values: dict[str, str]) -> Credential:
        username = form_values.get("username", "").strip()
        password = form_values.get("password", "").strip()
        if not username or not password:
            raise AuthError("Email and password are both required.")
        return Credential(provider_key=self._provider_key, data={"username": username, "password": password})

    def refresh(self, credential: Credential) -> Credential:
        return credential  # app passwords don't expire
