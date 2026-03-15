# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import csv
import datetime
import gzip
from pathlib import Path

import pytest

from aol_email_exporter.exporters.csv_export import CsvExporter
from aol_email_exporter.exporters.excel_export import ExcelExporter
from aol_email_exporter.exporters.pdf_export import PdfExporter
from aol_email_exporter.filters import apply_filters
from aol_email_exporter.models import EmailRecord, ExportConfig, FilterParams

openpyxl = pytest.importorskip("openpyxl")

pytestmark = pytest.mark.tier_b


def _record(**overrides) -> EmailRecord:
    """Build an EmailRecord with sensible defaults, overriding as needed."""
    defaults = {
        "uid": "edge-1",
        "date": datetime.datetime(2024, 3, 15, 12, 0, tzinfo=datetime.UTC),
        "sender": "test@aol.com",
        "to": "me@aol.com",
        "cc": "",
        "subject": "Edge case test",
        "body_text": "Default body.",
        "body_html": "",
        "folder": "INBOX",
        "has_attachments": False,
        "message_id": "<edge-1@aol.com>",
        "size_bytes": 128,
    }
    defaults.update(overrides)
    return EmailRecord(**defaults)


def _csv_config(tmp_path) -> ExportConfig:
    return ExportConfig(output_dir=str(tmp_path), formats=("csv",), filename_prefix="edge_csv")


def _excel_config(tmp_path) -> ExportConfig:
    return ExportConfig(output_dir=str(tmp_path), formats=("excel",), filename_prefix="edge_xlsx")


def _pdf_config(tmp_path) -> ExportConfig:
    return ExportConfig(output_dir=str(tmp_path), formats=("pdf",), filename_prefix="edge_pdf")


class TestEdgeCases:
    """Boundary conditions and adversarial inputs."""

    def test_unicode_subject_csv(self, tmp_path):
        rec = _record(uid="u1", subject="Meeting \u4f1a\u8bae \U0001f4e7 caf\u00e9")
        result = CsvExporter().export([rec], _csv_config(tmp_path))
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["subject"] == "Meeting \u4f1a\u8bae \U0001f4e7 caf\u00e9"

    def test_unicode_body_excel(self, tmp_path):
        rec = _record(uid="u2", body_text="R\u00e9sum\u00e9 with \u00fc\u00f6\u00e4 and \u00f1")
        result = ExcelExporter().export([rec], _excel_config(tmp_path))
        wb = openpyxl.load_workbook(result.file_path)
        ws = wb.active
        # Body text is in the body_text column (index depends on header order)
        headers = [cell.value for cell in ws[1]]
        body_idx = headers.index("body_text") + 1
        assert ws.cell(row=2, column=body_idx).value == "R\u00e9sum\u00e9 with \u00fc\u00f6\u00e4 and \u00f1"
        wb.close()

    def test_empty_body_email(self, tmp_path):
        rec = _record(uid="u3", body_text="", body_html="")
        result = CsvExporter().export([rec], _csv_config(tmp_path))
        assert result.success is True
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["body_text"] == ""
        assert row["body_html"] == ""

    def test_html_only_email(self, tmp_path):
        rec = _record(uid="u4", body_text="", body_html="<p>HTML only content</p>")
        result = CsvExporter().export([rec], _csv_config(tmp_path))
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["body_text"] == ""
        assert row["body_html"] == "<p>HTML only content</p>"

    def test_very_long_subject(self, tmp_path):
        long_subject = "A" * 500
        rec = _record(uid="u5", subject=long_subject)
        # CSV
        csv_result = CsvExporter().export([rec], _csv_config(tmp_path))
        assert csv_result.success is True
        # Excel
        excel_result = ExcelExporter().export(
            [rec],
            ExportConfig(output_dir=str(tmp_path), formats=("excel",), filename_prefix="edge_long_xlsx"),
        )
        assert excel_result.success is True
        # PDF
        pdf_result = PdfExporter().export(
            [rec],
            ExportConfig(output_dir=str(tmp_path), formats=("pdf",), filename_prefix="edge_long_pdf"),
        )
        assert pdf_result.success is True

    def test_special_chars_in_sender(self, tmp_path):
        rec = _record(uid="u6", sender='"O\'Brien, Bob" <bob.obrien@example.com>')
        result = CsvExporter().export([rec], _csv_config(tmp_path))
        assert result.success is True
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert "O'Brien" in row["sender"]

    def test_date_boundary_filter(self):
        """date_from == date_to: apply_filters does client-side sender/subject
        only; date filtering is server-side. Verify no crash and passthrough."""
        rec = _record(uid="u7", date=datetime.datetime(2024, 3, 15, 12, 0, tzinfo=datetime.UTC))
        params = FilterParams(
            date_from=datetime.date(2024, 3, 15),
            date_to=datetime.date(2024, 3, 15),
        )
        result = apply_filters([rec], params)
        # apply_filters passes through (no sender/subject filter)
        assert len(result) == 1

    def test_future_date_filter(self):
        """Future sender that matches no records returns empty."""
        rec = _record(uid="u8")
        params = FilterParams(sender="nobody@year3000.future")
        result = apply_filters([rec], params)
        assert result == []

    def test_zero_size_email(self, tmp_path):
        rec = _record(uid="u9", size_bytes=0)
        csv_result = CsvExporter().export([rec], _csv_config(tmp_path))
        assert csv_result.success is True
        with gzip.open(csv_result.file_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["size_bytes"] == "0"
