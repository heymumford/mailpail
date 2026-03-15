# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from operator import attrgetter

from mailpail.models import EmailRecord, FilterParams

logger = logging.getLogger(__name__)

_SORT_KEYS = frozenset({"date", "sender", "subject", "folder", "size_bytes"})


def apply_filters(records: list[EmailRecord], filters: FilterParams) -> list[EmailRecord]:
    """Refine *records* with client-side substring matching.

    IMAP server-side search is coarse; this pass enforces case-insensitive
    substring matching on sender and subject for exact user intent.
    """
    result = records

    if filters.sender:
        needle = filters.sender.lower()
        result = [r for r in result if needle in r.sender.lower()]
        logger.debug("Sender filter '%s' reduced set to %d records", filters.sender, len(result))

    if filters.subject:
        needle = filters.subject.lower()
        result = [r for r in result if needle in r.subject.lower()]
        logger.debug("Subject filter '%s' reduced set to %d records", filters.subject, len(result))

    if len(result) != len(records):
        logger.info("Post-fetch filtering: %d -> %d records", len(records), len(result))

    return result


def sort_records(records: list[EmailRecord], key: str = "date", reverse: bool = False) -> list[EmailRecord]:
    """Sort *records* by the given attribute name.

    Supported keys: date, sender, subject, folder, size_bytes.
    """
    if key not in _SORT_KEYS:
        raise ValueError(f"Unsupported sort key '{key}'. Choose from: {', '.join(sorted(_SORT_KEYS))}")

    return sorted(records, key=attrgetter(key), reverse=reverse)
