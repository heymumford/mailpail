# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import pytest

from mailpail.exporters.eml_export import EmlExporter
from mailpail.models import ExportConfig

pytestmark = pytest.mark.tier_a


def _export(records, tmp_path, **overrides):
    defaults = {"output_dir": str(tmp_path), "formats": ("eml",), "filename_prefix": "test_eml"}
    defaults.update(overrides)
    config = ExportConfig(**defaults)
    return EmlExporter().export(records, config)


class TestEmlExporter:
    def test_export_creates_eml_directory(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        path = Path(result.file_path)
        assert path.is_dir()

    def test_export_file_count(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        eml_files = list(Path(result.file_path).glob("*.eml"))
        assert len(eml_files) == len(sample_records)

    def test_export_eml_content(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        eml_files = list(Path(result.file_path).glob("*.eml"))
        all_content = "".join(f.read_text(encoding="utf-8", errors="replace") for f in eml_files)
        # Every subject from sample_records should appear in at least one EML file
        for rec in sample_records:
            assert rec.subject in all_content, f"Subject {rec.subject!r} not found in EML output"

    def test_export_result_metadata(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        assert result.format_name == "eml"
        assert result.record_count == len(sample_records)
        assert result.success is True
        assert result.sha256 != ""

    def test_export_empty_records(self, empty_records, tmp_path):
        result = _export(empty_records, tmp_path)
        assert result.success is True
        assert result.record_count == 0
