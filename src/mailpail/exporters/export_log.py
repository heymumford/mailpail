# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Structured export log — machine-parseable audit of every export run."""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path

from mailpail.models import ExportResult, FilterParams

logger = logging.getLogger(__name__)


def write_export_log(
    output_dir: Path,
    results: list[ExportResult],
    total_emails: int,
    filters: FilterParams | None = None,
    folders: list[str] | None = None,
    provider_key: str = "",
    username: str = "",
    filename: str = "export_log.json",
) -> Path:
    """Write a structured export log to output_dir.

    Contains timestamps, filter criteria, result counts, errors, and warnings.
    This is the audit artifact Sandra needs for legal use.
    """
    log_path = output_dir / filename
    now = datetime.datetime.now(datetime.UTC)

    export_entries = []
    for r in results:
        entry: dict = {
            "format": r.format_name,
            "file_path": r.file_path,
            "record_count": r.record_count,
            "attachment_count": r.attachment_count,
            "success": r.success,
        }
        if r.error:
            entry["error"] = r.error
        if r.warnings:
            entry["warnings"] = r.warnings
        if r.sha256:
            entry["sha256"] = r.sha256
        export_entries.append(entry)

    filter_info: dict = {}
    if filters:
        if filters.date_from:
            filter_info["date_from"] = filters.date_from.isoformat()
        if filters.date_to:
            filter_info["date_to"] = filters.date_to.isoformat()
        if filters.sender:
            filter_info["sender"] = filters.sender
        if filters.subject:
            filter_info["subject"] = filters.subject
        if filters.unread_only:
            filter_info["unread_only"] = True

    log_data = {
        "mailpail_version": _get_version(),
        "timestamp_utc": now.isoformat(),
        "provider": provider_key,
        "username": username,
        "folders_exported": folders or [],
        "filters_applied": filter_info,
        "total_emails_matched": total_emails,
        "exports": export_entries,
        "success": all(r.success for r in results),
    }

    log_path.write_text(json.dumps(log_data, indent=2) + "\n", encoding="utf-8")
    logger.info("Export log written to %s", log_path)
    return log_path


def _get_version() -> str:
    try:
        from mailpail import __version__

        return __version__
    except ImportError:
        return "unknown"
