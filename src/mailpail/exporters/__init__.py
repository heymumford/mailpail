# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from mailpail.models import EmailRecord, ExportConfig, ExportResult

logger = logging.getLogger(__name__)

EXPORTER_ENTRY_POINT_GROUP = "mailpail.exporters"


@runtime_checkable
class BaseExporter(Protocol):
    """Contract that every exporter must satisfy."""

    def export(self, records: list[EmailRecord], config: ExportConfig) -> ExportResult: ...


# Lazy imports so missing optional deps don't blow up on import.
def _load_exporters() -> dict[str, type]:
    from mailpail.exporters.csv_export import CsvExporter
    from mailpail.exporters.eml_export import EmlExporter
    from mailpail.exporters.excel_export import ExcelExporter, ExcelSheetsExporter
    from mailpail.exporters.mbox_export import MboxExporter
    from mailpail.exporters.pdf_export import PdfExporter

    return {
        "csv": CsvExporter,
        "excel": ExcelExporter,
        "excel-sheets": ExcelSheetsExporter,
        "pdf": PdfExporter,
        "mbox": MboxExporter,
        "eml": EmlExporter,
    }


def _load_plugin_exporters() -> dict[str, type]:
    """Discover third-party exporter plugins via entry points."""
    import importlib.metadata

    plugins: dict[str, type] = {}
    try:
        eps = importlib.metadata.entry_points(group=EXPORTER_ENTRY_POINT_GROUP)
        for ep in eps:
            try:
                cls = ep.load()
                plugins[ep.name] = cls
                logger.info("Loaded exporter plugin: %s (%s)", ep.name, ep.value)
            except Exception:
                logger.warning("Failed to load exporter plugin: %s", ep.name, exc_info=True)
    except Exception:
        pass
    return plugins


EXPORTERS: dict[str, type] = {}


def get_exporter(format_name: str) -> BaseExporter:
    """Return an exporter instance for *format_name*.

    Raises KeyError if the format is not registered.
    """
    global EXPORTERS  # noqa: PLW0603
    if not EXPORTERS:
        EXPORTERS.update(_load_exporters())
        EXPORTERS.update(_load_plugin_exporters())

    cls = EXPORTERS.get(format_name)
    if cls is None:
        raise KeyError(f"Unknown export format '{format_name}'. Available: {', '.join(sorted(EXPORTERS))}")
    return cls()


def available_formats() -> list[str]:
    """Return sorted list of all registered export format names."""
    global EXPORTERS  # noqa: PLW0603
    if not EXPORTERS:
        EXPORTERS.update(_load_exporters())
        EXPORTERS.update(_load_plugin_exporters())
    return sorted(EXPORTERS.keys())
