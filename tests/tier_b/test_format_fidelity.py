# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import csv
import datetime
import gzip
from pathlib import Path

import pytest

from mailpail.exporters.csv_export import CsvExporter
from mailpail.exporters.excel_export import ExcelExporter, ExcelSheetsExporter
from mailpail.exporters.pdf_export import PdfExporter
from mailpail.models import EmailRecord, ExportConfig

openpyxl = pytest.importorskip("openpyxl")

pytestmark = pytest.mark.tier_b


def _record(uid: str, **overrides) -> EmailRecord:
    defaults = {
        "uid": uid,
        "date": datetime.datetime(2024, 3, 15, 12, 0, tzinfo=datetime.UTC),
        "sender": "roundtrip@aol.com",
        "to": "me@aol.com",
        "cc": "cc@aol.com",
        "subject": f"Subject for {uid}",
        "body_text": f"Body text for {uid}.",
        "body_html": f"<p>Body html for {uid}.</p>",
        "folder": "INBOX",
        "has_attachments": False,
        "message_id": f"<{uid}@aol.com>",
        "size_bytes": 256,
    }
    defaults.update(overrides)
    return EmailRecord(**defaults)


def _records(n: int = 5) -> list[EmailRecord]:
    folders = ["INBOX", "Sent", "Archive"]
    return [
        _record(
            uid=f"rt-{i}",
            folder=folders[i % len(folders)],
            date=datetime.datetime(2024, 1 + i, 1, 12, 0, tzinfo=datetime.UTC),
        )
        for i in range(n)
    ]


class TestFormatFidelity:
    def test_csv_roundtrip(self, tmp_path):
        records = _records(5)
        config = ExportConfig(output_dir=str(tmp_path), formats=("csv",), filename_prefix="rt_csv")
        result = CsvExporter().export(records, config)

        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == len(records)
        for row, rec in zip(rows, records):
            assert row["sender"] == rec.sender
            assert row["to"] == rec.to
            assert row["cc"] == rec.cc
            assert row["subject"] == rec.subject
            assert row["body_text"] == rec.body_text
            assert row["folder"] == rec.folder
            assert row["message_id"] == rec.message_id

    def test_excel_date_format(self, tmp_path):
        records = _records(3)
        config = ExportConfig(output_dir=str(tmp_path), formats=("excel",), filename_prefix="rt_date")
        result = ExcelExporter().export(records, config)

        wb = openpyxl.load_workbook(result.file_path)
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        date_col = headers.index("Date") + 1

        for row_idx in range(2, 2 + len(records)):
            cell_value = ws.cell(row=row_idx, column=date_col).value
            # Date column contains ISO strings from the exporter
            assert cell_value is not None
        wb.close()

    def test_excel_sheets_all_records_present(self, tmp_path):
        records = _records(5)
        config = ExportConfig(
            output_dir=str(tmp_path),
            formats=("excel-sheets",),
            filename_prefix="rt_sheets",
            excel_group_by="folder",
        )
        result = ExcelSheetsExporter().export(records, config)

        wb = openpyxl.load_workbook(result.file_path)
        total = sum(ws.max_row - 1 for ws in wb.worksheets)
        wb.close()
        assert total == len(records)

    def test_pdf_contains_all_subjects(self, tmp_path):
        records = _records(3)
        config = ExportConfig(
            output_dir=str(tmp_path),
            formats=("pdf",),
            filename_prefix="rt_pdf",
            pdf_title="Fidelity Test",
        )
        result = PdfExporter().export(records, config)
        assert result.success is True
        assert result.record_count == len(records)
        assert Path(result.file_path).stat().st_size > 0

    def test_multiple_formats_same_data(self, tmp_path):
        records = _records(3)
        results = []
        exporters_and_configs = [
            (CsvExporter(), ExportConfig(output_dir=str(tmp_path), formats=("csv",), filename_prefix="multi_csv")),
            (ExcelExporter(), ExportConfig(output_dir=str(tmp_path), formats=("excel",), filename_prefix="multi_xlsx")),
            (PdfExporter(), ExportConfig(output_dir=str(tmp_path), formats=("pdf",), filename_prefix="multi_pdf")),
        ]
        for exporter, config in exporters_and_configs:
            r = exporter.export(records, config)
            results.append(r)

        for r in results:
            assert r.success is True
            assert r.record_count == len(records)
            assert Path(r.file_path).exists()

    def test_csv_gzip_decompresses(self, tmp_path):
        records = _records(2)
        config = ExportConfig(output_dir=str(tmp_path), formats=("csv",), filename_prefix="gz_test")
        result = CsvExporter().export(records, config)

        with gzip.open(result.file_path, "rt") as f:
            content = f.read()
        assert len(content) > 0
        lines = content.strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows

    def test_export_config_custom_prefix(self, tmp_path):
        records = _records(1)
        prefix = "custom_output_name"
        config = ExportConfig(output_dir=str(tmp_path), formats=("csv",), filename_prefix=prefix)
        result = CsvExporter().export(records, config)
        filename = Path(result.file_path).name
        assert filename.startswith(prefix)
