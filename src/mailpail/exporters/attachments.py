# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Attachment saving utility — writes attachment bytes to disk."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from mailpail.models import EmailRecord

logger = logging.getLogger(__name__)

_SAFE_CHARS = re.compile(r"[^\w\s\-.]")
_MAX_FILENAME_LEN = 80


def _safe_name(name: str) -> str:
    """Make a filename filesystem-safe."""
    clean = _SAFE_CHARS.sub("_", name).strip()
    return clean[:_MAX_FILENAME_LEN] if clean else "unnamed"


def save_attachments(records: list[EmailRecord], output_dir: Path) -> int:
    """Save all attachments from *records* into output_dir/attachments/.

    Files are organized as: attachments/{uid}_{filename}
    Idempotent — skips files that already exist (safe for multi-format runs).
    Returns total number of attachments saved.
    """
    att_dir = output_dir / "attachments"
    has_atts = any(rec.attachments for rec in records)
    if not has_atts:
        return 0

    att_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for rec in records:
        if not rec.attachments:
            continue
        for att in rec.attachments:
            safe = _safe_name(att.filename)
            dest = att_dir / f"{rec.uid}_{safe}"
            # Skip if already written (idempotent for multi-format runs)
            if dest.exists():
                count += 1
                continue
            dest.write_bytes(att.payload)
            count += 1

    if count:
        logger.info("Saved %d attachments to %s", count, att_dir)
    return count


def attachment_filenames(rec: EmailRecord) -> str:
    """Return a semicolon-separated list of attachment filenames for a record."""
    if not rec.attachments:
        return ""
    return "; ".join(a.filename for a in rec.attachments)
