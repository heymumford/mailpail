# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import mailbox
from pathlib import Path

import pytest

from mailpail.exporters.mbox_export import MboxExporter
from mailpail.models import ExportConfig

pytestmark = pytest.mark.tier_a


def _export(records, tmp_path, **overrides):
    defaults = {"output_dir": str(tmp_path), "formats": ("mbox",), "filename_prefix": "test_mbox"}
    defaults.update(overrides)
    config = ExportConfig(**defaults)
    return MboxExporter().export(records, config)


class TestMboxExporter:
    def test_export_creates_mbox_file(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        path = Path(result.file_path)
        assert path.exists()
        assert path.suffix == ".mbox"

    def test_export_message_count(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        mbox = mailbox.mbox(result.file_path)
        assert len(mbox) == len(sample_records)
        mbox.close()

    def test_export_preserves_sender(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        mbox = mailbox.mbox(result.file_path)
        first = mbox[0]
        assert sample_records[0].sender in first["From"]
        mbox.close()

    def test_export_preserves_subject(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        mbox = mailbox.mbox(result.file_path)
        first = mbox[0]
        assert first["Subject"] == sample_records[0].subject
        mbox.close()

    def test_export_result_metadata(self, sample_records, tmp_path):
        result = _export(sample_records, tmp_path)
        assert result.format_name == "mbox"
        assert result.record_count == len(sample_records)
        assert result.success is True
        assert result.sha256 != ""

    def test_export_empty_records(self, empty_records, tmp_path):
        result = _export(empty_records, tmp_path)
        assert result.success is True
        assert result.record_count == 0
