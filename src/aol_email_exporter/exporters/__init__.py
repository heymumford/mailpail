# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aol_email_exporter.models import EmailRecord, ExportConfig, ExportResult


@runtime_checkable
class BaseExporter(Protocol):
    """Contract that every exporter must satisfy."""

    def export(self, records: list[EmailRecord], config: ExportConfig) -> ExportResult: ...


# Lazy imports so missing optional deps don't blow up on import.
def _load_exporters() -> dict[str, type]:
    from aol_email_exporter.exporters.csv_export import CsvExporter
    from aol_email_exporter.exporters.excel_export import ExcelExporter, ExcelSheetsExporter
    from aol_email_exporter.exporters.pdf_export import PdfExporter

    return {
        "csv": CsvExporter,
        "excel": ExcelExporter,
        "excel-sheets": ExcelSheetsExporter,
        "pdf": PdfExporter,
    }


EXPORTERS: dict[str, type] = {}


def get_exporter(format_name: str) -> BaseExporter:
    """Return an exporter instance for *format_name*.

    Raises KeyError if the format is not registered.
    """
    global EXPORTERS  # noqa: PLW0603
    if not EXPORTERS:
        EXPORTERS.update(_load_exporters())

    cls = EXPORTERS.get(format_name)
    if cls is None:
        raise KeyError(f"Unknown export format '{format_name}'. Available: {', '.join(sorted(EXPORTERS))}")
    return cls()
