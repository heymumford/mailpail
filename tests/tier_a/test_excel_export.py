# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import pytest

from mailpail.exporters.excel_export import ExcelExporter, ExcelSheetsExporter
from mailpail.models import ExportConfig

openpyxl = pytest.importorskip("openpyxl")

pytestmark = pytest.mark.tier_a

EXPECTED_HEADERS = [
    "Date",
    "From",
    "To",
    "CC",
    "Subject",
    "Body",
    "Folder",
    "Attachments",
    "Attachment Files",
    "Message-ID",
]


def _export_single(records, tmp_path, **overrides):
    defaults = {
        "output_dir": str(tmp_path),
        "formats": ("excel",),
        "filename_prefix": "test_excel",
    }
    defaults.update(overrides)
    config = ExportConfig(**defaults)
    exporter = ExcelExporter()
    return exporter.export(records, config)


def _export_sheets(records, tmp_path, **overrides):
    defaults = {
        "output_dir": str(tmp_path),
        "formats": ("excel-sheets",),
        "filename_prefix": "test_excel_sheets",
        "excel_group_by": "folder",
    }
    defaults.update(overrides)
    config = ExportConfig(**defaults)
    exporter = ExcelSheetsExporter()
    return exporter.export(records, config)


class TestExcelExporter:
    """Single-sheet Excel exporter."""

    def test_export_creates_xlsx(self, sample_records, tmp_path):
        result = _export_single(sample_records, tmp_path)
        path = Path(result.file_path)
        assert path.exists()
        assert path.suffix == ".xlsx"
        # Validate it opens as a workbook
        wb = openpyxl.load_workbook(path)
        wb.close()

    def test_export_headers(self, sample_records, tmp_path):
        result = _export_single(sample_records, tmp_path)
        wb = openpyxl.load_workbook(result.file_path)
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        wb.close()
        assert headers == EXPECTED_HEADERS

    def test_export_row_count(self, sample_records, tmp_path):
        result = _export_single(sample_records, tmp_path)
        wb = openpyxl.load_workbook(result.file_path)
        ws = wb.active
        data_rows = ws.max_row - 1  # subtract header row
        wb.close()
        assert data_rows == len(sample_records)

    def test_export_autofilter(self, sample_records, tmp_path):
        result = _export_single(sample_records, tmp_path)
        wb = openpyxl.load_workbook(result.file_path)
        ws = wb.active
        assert ws.auto_filter.ref is not None and ws.auto_filter.ref != ""
        wb.close()

    def test_export_frozen_panes(self, sample_records, tmp_path):
        result = _export_single(sample_records, tmp_path)
        wb = openpyxl.load_workbook(result.file_path)
        ws = wb.active
        # Frozen at row 2 means top row is frozen
        assert ws.freeze_panes is not None
        assert ws.freeze_panes == "A2"
        wb.close()

    def test_export_empty_records(self, empty_records, tmp_path):
        result = _export_single(empty_records, tmp_path)
        assert result.success is True
        assert result.record_count == 0
        wb = openpyxl.load_workbook(result.file_path)
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        assert headers == EXPECTED_HEADERS
        assert ws.max_row == 1  # headers only
        wb.close()


class TestExcelSheetsExporter:
    """Multi-sheet Excel exporter grouped by a field."""

    def test_export_creates_xlsx(self, sample_records, tmp_path):
        result = _export_sheets(sample_records, tmp_path)
        path = Path(result.file_path)
        assert path.exists()
        assert path.suffix == ".xlsx"

    def test_sheets_by_folder(self, sample_records, tmp_path):
        result = _export_sheets(sample_records, tmp_path, excel_group_by="folder")
        wb = openpyxl.load_workbook(result.file_path)
        sheet_names = set(wb.sheetnames)
        expected_folders = {r.folder for r in sample_records}
        wb.close()
        assert sheet_names == expected_folders

    def test_sheets_by_sender(self, sample_records, tmp_path):
        result = _export_sheets(sample_records, tmp_path, excel_group_by="sender")
        wb = openpyxl.load_workbook(result.file_path)
        sheet_names = set(wb.sheetnames)
        expected_senders = {r.sender for r in sample_records}
        wb.close()
        # Sheet names may be truncated, but count must match
        assert len(sheet_names) == len(expected_senders)

    def test_sheet_row_counts(self, sample_records, tmp_path):
        result = _export_sheets(sample_records, tmp_path, excel_group_by="folder")
        wb = openpyxl.load_workbook(result.file_path)
        total_data_rows = 0
        for ws in wb.worksheets:
            total_data_rows += ws.max_row - 1  # subtract header per sheet
        wb.close()
        assert total_data_rows == len(sample_records)

    def test_sheet_names_sanitized(self, sample_records, tmp_path):
        result = _export_sheets(sample_records, tmp_path)
        wb = openpyxl.load_workbook(result.file_path)
        invalid_chars = {"\\", "/", "*", "?", ":", "[", "]"}
        for name in wb.sheetnames:
            assert len(name) <= 31, f"Sheet name too long: {name!r}"
            assert not invalid_chars & set(name), f"Invalid chars in sheet name: {name!r}"
        wb.close()
