# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Incremental export — track which emails have been exported by UID.

Stores a .mailpail_exported file in the output directory containing
one UID per line. On subsequent runs, already-exported UIDs are skipped.
"""

from __future__ import annotations

import logging
from pathlib import Path

from mailpail.models import EmailRecord

logger = logging.getLogger(__name__)

_STATE_FILE = ".mailpail_exported"


def load_exported_uids(output_dir: Path) -> set[str]:
    """Load the set of previously exported UIDs from the state file."""
    state_file = output_dir / _STATE_FILE
    if not state_file.exists():
        return set()
    uids = set()
    for line in state_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            uids.add(line)
    logger.info("Loaded %d previously exported UIDs from %s", len(uids), state_file)
    return uids


def save_exported_uids(output_dir: Path, uids: set[str]) -> Path:
    """Save the set of exported UIDs to the state file (appends new UIDs)."""
    state_file = output_dir / _STATE_FILE
    existing = load_exported_uids(output_dir)
    all_uids = existing | uids
    state_file.write_text("\n".join(sorted(all_uids)) + "\n", encoding="utf-8")
    new_count = len(all_uids) - len(existing)
    logger.info("Saved %d UIDs (%d new) to %s", len(all_uids), new_count, state_file)
    return state_file


def filter_new_records(records: list[EmailRecord], output_dir: Path) -> list[EmailRecord]:
    """Return only records whose UIDs haven't been exported yet."""
    exported = load_exported_uids(output_dir)
    if not exported:
        return records
    new = [r for r in records if r.uid not in exported]
    skipped = len(records) - len(new)
    if skipped:
        logger.info("Incremental: skipping %d already-exported emails, %d new", skipped, len(new))
    return new
