# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Export manifest — summary of all exported files with sizes and hashes."""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
from pathlib import Path

from mailpail.models import ExportResult

logger = logging.getLogger(__name__)


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    output_dir: Path,
    results: list[ExportResult],
    total_emails: int,
    filename: str = "manifest.json",
) -> Path:
    """Write a JSON manifest of the export to output_dir/manifest.json.

    Includes file list with sizes and SHA-256 hashes.
    Returns the path to the manifest file.
    """
    manifest_path = output_dir / filename

    files = []
    for r in results:
        if not r.success:
            continue
        rp = Path(r.file_path)
        if rp.is_file():
            files.append(
                {
                    "format": r.format_name,
                    "path": rp.name,
                    "size_bytes": rp.stat().st_size,
                    "sha256": _sha256_file(rp),
                    "record_count": r.record_count,
                    "attachment_count": r.attachment_count,
                }
            )
        elif rp.is_dir():
            # EML exporter creates a directory
            dir_files = sorted(rp.rglob("*"))
            total_size = sum(f.stat().st_size for f in dir_files if f.is_file())
            file_count = sum(1 for f in dir_files if f.is_file())
            files.append(
                {
                    "format": r.format_name,
                    "path": rp.name,
                    "size_bytes": total_size,
                    "file_count": file_count,
                    "sha256": r.sha256,
                    "record_count": r.record_count,
                    "attachment_count": r.attachment_count,
                }
            )

    # Attachment directory
    att_dir = output_dir / "attachments"
    if att_dir.is_dir():
        att_files = sorted(att_dir.rglob("*"))
        att_file_list = [f for f in att_files if f.is_file()]
        if att_file_list:
            files.append(
                {
                    "format": "attachments",
                    "path": "attachments",
                    "size_bytes": sum(f.stat().st_size for f in att_file_list),
                    "file_count": len(att_file_list),
                }
            )

    manifest = {
        "mailpail_version": _get_version(),
        "generated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "total_emails": total_emails,
        "exports": files,
    }

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info("Manifest written to %s", manifest_path)
    return manifest_path


def _get_version() -> str:
    try:
        from mailpail import __version__

        return __version__
    except ImportError:
        return "unknown"
