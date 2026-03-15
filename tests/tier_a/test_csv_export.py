# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import csv
import gzip
from pathlib import Path

import pytest

from aol_email_exporter.exporters.csv_export import CsvExporter
from aol_email_exporter.models import ExportConfig


pytestmark = pytest.mark.tier_a

EXPECTED_HEADERS = [
    "uid",
    "date",
    "sender",
    "to",
    "cc",
    "subject",
    "body_text",
    "body_html",
    "folder",
    "has_attachments",
    "message_id",
    "size_bytes",
]


def _export(records, tmp_path, **overrides) -> tuple:
    """Run CsvExporter and return (result, output_dir)."""
    defaults = {
        "output_dir": str(tmp_path),
        "formats": ("csv",),
        "filename_prefix": "test_csv",
    }
    defaults.update(overrides)
    config = ExportConfig(**defaults)
    exporter = CsvExporter()
    result = exporter.export(records, config)
    return result, tmp_path


class TestCsvExporter:
    """CSV exporter produces valid gzipped CSV files."""

    def test_export_creates_gzip_file(self, sample_records, tmp_path):
        result, _ = _export(sample_records, tmp_path)
        path = Path(result.file_path)
        assert path.exists()
        # Verify it is valid gzip by opening it
        with gzip.open(path, "rt") as f:
            content = f.read()
        assert len(content) > 0

    def test_export_csv_headers(self, sample_records, tmp_path):
        result, _ = _export(sample_records, tmp_path)
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
        assert headers == EXPECTED_HEADERS

    def test_export_csv_row_count(self, sample_records, tmp_path):
        result, _ = _export(sample_records, tmp_path)
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            rows = list(reader)
        assert len(rows) == len(sample_records)

    def test_export_csv_content(self, sample_records, tmp_path):
        result, _ = _export(sample_records, tmp_path)
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        first = rows[0]
        rec = sample_records[0]
        assert first["uid"] == rec.uid
        assert first["sender"] == rec.sender
        assert first["subject"] == rec.subject
        assert first["folder"] == rec.folder

    def test_export_result_metadata(self, sample_records, tmp_path):
        result, _ = _export(sample_records, tmp_path)
        assert result.format_name == "csv"
        assert result.record_count == len(sample_records)
        assert result.success is True
        assert result.error is None

    def test_export_empty_records(self, empty_records, tmp_path):
        result, _ = _export(empty_records, tmp_path)
        assert result.success is True
        assert result.record_count == 0
        with gzip.open(result.file_path, "rt", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            data_rows = list(reader)
        assert headers == EXPECTED_HEADERS
        assert len(data_rows) == 0
