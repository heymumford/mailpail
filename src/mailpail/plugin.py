# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Plugin discovery — load third-party provider adapters via entry points.

Plugin packages register themselves under the ``mailpail.providers`` entry
point group. Each entry point must resolve to a ``ProviderDescriptor`` instance.

Example plugin ``pyproject.toml``::

    [project.entry-points."mailpail.providers"]
    gmail-oauth = "mailpail_gmail_oauth.descriptor:DESCRIPTOR"

The core calls ``load_plugins()`` once at startup. Zero plugins installed
means zero iterations, zero overhead.
"""

from __future__ import annotations

import importlib.metadata
import logging

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "mailpail.providers"

_loaded = False


def load_plugins() -> None:
    """Discover and register installed plugin providers.

    Safe to call multiple times (idempotent). Errors from individual
    plugins are logged and skipped — they never prevent the core from starting.
    """
    global _loaded  # noqa: PLW0603
    if _loaded:
        return
    _loaded = True

    from mailpail.providers import PROVIDERS, ProviderDescriptor

    for ep in importlib.metadata.entry_points(group=ENTRY_POINT_GROUP):
        if ep.name in PROVIDERS:
            logger.debug("Plugin %r skipped — built-in provider takes precedence", ep.name)
            continue
        try:
            descriptor = ep.load()
            if not isinstance(descriptor, ProviderDescriptor):
                logger.warning("Plugin %r did not provide a ProviderDescriptor — skipped", ep.name)
                continue
            PROVIDERS[descriptor.key] = descriptor
            logger.debug("Registered plugin provider %r from %r", descriptor.key, ep.value)
        except Exception:
            logger.warning("Failed to load plugin provider %r", ep.name, exc_info=True)
