# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Data models for AOL Email Exporter."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmailRecord:
    """Immutable representation of a fetched email."""

    uid: str
    date: datetime.datetime
    sender: str
    to: str
    cc: str
    subject: str
    body_text: str
    body_html: str
    folder: str
    has_attachments: bool
    message_id: str
    size_bytes: int = 0


@dataclass(frozen=True)
class FilterParams:
    """Criteria for selecting emails from the server."""

    date_from: datetime.date | None = None
    date_to: datetime.date | None = None
    sender: str | None = None
    subject: str | None = None
    folder: str | None = None
    unread_only: bool = False


@dataclass(frozen=True)
class ExportConfig:
    """Configuration for export operations."""

    output_dir: str = "./export"
    formats: tuple[str, ...] = ("csv",)
    excel_group_by: str = "folder"
    pdf_title: str = "AOL Email Export"
    filename_prefix: str = "aol_export"


@dataclass
class ExportResult:
    """Outcome of an export operation."""

    format_name: str
    file_path: str
    record_count: int
    success: bool
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
