# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import csv
import gzip
import logging
from pathlib import Path

from aol_email_exporter.models import EmailRecord, ExportConfig, ExportResult

logger = logging.getLogger(__name__)

_COLUMNS = [
    "date",
    "sender",
    "to",
    "cc",
    "subject",
    "body_text",
    "folder",
    "has_attachments",
    "message_id",
]


class CsvExporter:
    """Export emails to gzip-compressed CSV."""

    def export(self, records: list[EmailRecord], config: ExportConfig) -> ExportResult:
        out_dir = Path(config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{config.filename_prefix}.csv.gz"

        warnings: list[str] = []
        try:
            with gzip.open(out_path, "wt", encoding="utf-8", newline="") as gz:
                writer = csv.writer(gz)
                writer.writerow(_COLUMNS)

                for rec in records:
                    writer.writerow(
                        [
                            rec.date.isoformat() if rec.date else "",
                            rec.sender,
                            rec.to,
                            rec.cc,
                            rec.subject,
                            rec.body_text,
                            rec.folder,
                            rec.has_attachments,
                            rec.message_id,
                        ]
                    )

            file_size = out_path.stat().st_size
            logger.info("CSV export complete: %d records, %s (%d bytes)", len(records), out_path, file_size)

            return ExportResult(
                format_name="csv",
                file_path=str(out_path),
                record_count=len(records),
                success=True,
                warnings=warnings,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("CSV export failed: %s", exc)
            return ExportResult(
                format_name="csv",
                file_path=str(out_path),
                record_count=0,
                success=False,
                error=str(exc),
                warnings=warnings,
            )
