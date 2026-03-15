# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import pytest

from aol_email_exporter.exporters.pdf_export import PdfExporter
from aol_email_exporter.models import ExportConfig


pytestmark = pytest.mark.tier_a


def _export(records, tmp_path, **overrides):
    defaults = {
        "output_dir": str(tmp_path),
        "formats": ("pdf",),
        "filename_prefix": "test_pdf",
        "pdf_title": "Test PDF Export",
    }
    defaults.update(overrides)
    config = ExportConfig(**defaults)
    exporter = PdfExporter()
    return exporter.export(records, config)


class TestPdfExporter:
    """PDF exporter produces valid PDF files."""

    def test_export_creates_pdf(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        path = Path(result.file_path)
        assert path.exists()
        # PDF files start with %PDF magic bytes
        with open(path, "rb") as f:
            magic = f.read(4)
        assert magic == b"%PDF"

    def test_export_result_success(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        assert result.success is True
        assert result.error is None
        assert result.format_name == "pdf"

    def test_export_nonempty(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        size = Path(result.file_path).stat().st_size
        assert size > 0

    def test_export_empty_records(self, empty_records, tmp_path):
        result = _export(empty_records, tmp_path)
        assert result.success is True
        path = Path(result.file_path)
        assert path.exists()
        with open(path, "rb") as f:
            magic = f.read(4)
        assert magic == b"%PDF"
