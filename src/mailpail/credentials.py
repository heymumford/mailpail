# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Credential storage — persistent storage for auth credentials between sessions.

Three concrete stores ship with core:
- ``EnvStore`` — reads from environment variables (CLI-friendly, read-only save)
- ``MemoryStore`` — in-process only (tests, single-session GUI)
- ``FileStore`` — JSON file at ``~/.mailpail/credentials.json``, mode 0600

Keyring support is deferred until a concrete use case demands it.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Protocol

from mailpail.auth import Credential

logger = logging.getLogger(__name__)


class CredentialStore(Protocol):
    """Persistent storage for credentials between sessions."""

    def save(self, credential: Credential) -> None: ...

    def load(self, provider_key: str) -> Credential | None: ...

    def delete(self, provider_key: str) -> None: ...


# ---------------------------------------------------------------------------
# EnvStore — read credentials from environment variables
# ---------------------------------------------------------------------------


class EnvStore:
    """Read-only credential store backed by environment variables.

    Loads ``MAILPAIL_{PROVIDER_KEY}_USERNAME`` and
    ``MAILPAIL_{PROVIDER_KEY}_PASSWORD`` (or ``MAILPAIL_APP_PASSWORD``
    as a fallback for the password).
    """

    def save(self, credential: Credential) -> None:
        logger.debug("EnvStore.save is a no-op (environment variables are read-only)")

    def load(self, provider_key: str) -> Credential | None:
        prefix = f"MAILPAIL_{provider_key.upper()}"
        username = os.environ.get(f"{prefix}_USERNAME", "")
        password = os.environ.get(f"{prefix}_PASSWORD", "") or os.environ.get("MAILPAIL_APP_PASSWORD", "")
        if username and password:
            return Credential(provider_key=provider_key, data={"username": username, "password": password})
        return None

    def delete(self, provider_key: str) -> None:
        logger.debug("EnvStore.delete is a no-op")


# ---------------------------------------------------------------------------
# MemoryStore — in-process only (tests, single-session use)
# ---------------------------------------------------------------------------


class MemoryStore:
    """In-memory credential store. Lost when the process exits."""

    def __init__(self) -> None:
        self._store: dict[str, Credential] = {}

    def save(self, credential: Credential) -> None:
        self._store[credential.provider_key] = credential

    def load(self, provider_key: str) -> Credential | None:
        return self._store.get(provider_key)

    def delete(self, provider_key: str) -> None:
        self._store.pop(provider_key, None)


# ---------------------------------------------------------------------------
# FileStore — JSON file with restrictive permissions
# ---------------------------------------------------------------------------

_DEFAULT_CRED_PATH = Path.home() / ".mailpail" / "credentials.json"


class FileStore:
    """JSON file credential store at ``~/.mailpail/credentials.json``.

    File permissions are set to 0600 (owner read/write only).
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DEFAULT_CRED_PATH

    def _read_all(self) -> dict[str, dict[str, str]]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read credential store at %s: %s", self._path, exc)
            return {}

    def _write_all(self, data: dict[str, dict[str, str]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.chmod(self._path, 0o600)
        except OSError:
            pass  # Windows may not support chmod

    def save(self, credential: Credential) -> None:
        data = self._read_all()
        data[credential.provider_key] = credential.data
        self._write_all(data)

    def load(self, provider_key: str) -> Credential | None:
        data = self._read_all()
        cred_data = data.get(provider_key)
        if cred_data is None:
            return None
        return Credential(provider_key=provider_key, data=cred_data)

    def delete(self, provider_key: str) -> None:
        data = self._read_all()
        if provider_key in data:
            del data[provider_key]
            self._write_all(data)
