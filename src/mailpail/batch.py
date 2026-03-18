# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Batch export — process multiple accounts from a CSV credential file.

CSV format (header required):
    username,password,provider,folder,format
    margaret@aol.com,abcd-efgh,aol,INBOX,csv
    derek@gmail.com,wxyz-1234,gmail,INBOX,excel

Only username and password are required. Other columns default to:
    provider=aol, folder=INBOX, format=csv
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatchEntry:
    """One account to export in a batch run."""

    username: str
    password: str
    provider: str = "aol"
    folder: str = "INBOX"
    format: str = "csv"


def load_batch_file(path: Path) -> list[BatchEntry]:
    """Parse a CSV credential file into BatchEntry objects.

    Raises ValueError if the file is missing required columns.
    """
    if not path.exists():
        raise FileNotFoundError(f"Batch file not found: {path}")

    entries: list[BatchEntry] = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError("Batch CSV file is empty")

        fields = {fn.strip().lower() for fn in reader.fieldnames}
        if "username" not in fields or "password" not in fields:
            raise ValueError("Batch CSV must have 'username' and 'password' columns")

        for row_num, row in enumerate(reader, start=2):
            # Normalize keys to lowercase for case-insensitive header matching
            norm = {k.strip().lower(): v for k, v in row.items() if k is not None}
            username = norm.get("username", "").strip()
            password = norm.get("password", "").strip()

            if not username or not password:
                logger.warning("Skipping row %d: missing username or password", row_num)
                continue

            entries.append(
                BatchEntry(
                    username=username,
                    password=password,
                    provider=norm.get("provider", "aol").strip() or "aol",
                    folder=norm.get("folder", "INBOX").strip() or "INBOX",
                    format=norm.get("format", "csv").strip() or "csv",
                )
            )

    logger.info("Loaded %d accounts from %s", len(entries), path)
    return entries
