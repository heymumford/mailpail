# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime
import json

import pytest

from mailpail.exporters.export_log import write_export_log
from mailpail.models import ExportResult, FilterParams

pytestmark = pytest.mark.tier_a


class TestExportLog:
    def test_creates_log_file(self, tmp_path):
        result = ExportResult(format_name="csv", file_path="/tmp/test.csv.gz", record_count=5, success=True)
        path = write_export_log(tmp_path, [result], total_emails=5)
        assert path.exists()
        assert path.name == "export_log.json"

    def test_log_structure(self, tmp_path):
        result = ExportResult(format_name="csv", file_path="/tmp/test.csv.gz", record_count=10, success=True)
        path = write_export_log(
            tmp_path,
            [result],
            total_emails=10,
            provider_key="aol",
            username="margaret@aol.com",
            folders=["INBOX", "Sent"],
        )
        data = json.loads(path.read_text())

        assert "mailpail_version" in data
        assert "timestamp_utc" in data
        assert data["provider"] == "aol"
        assert data["username"] == "margaret@aol.com"
        assert data["folders_exported"] == ["INBOX", "Sent"]
        assert data["total_emails_matched"] == 10
        assert data["success"] is True
        assert len(data["exports"]) == 1

    def test_log_includes_filter_criteria(self, tmp_path):
        filters = FilterParams(
            date_from=datetime.date(2024, 1, 1),
            date_to=datetime.date(2024, 12, 31),
            sender="alice@aol.com",
            subject="invoice",
        )
        result = ExportResult(format_name="csv", file_path="/tmp/test.csv.gz", record_count=3, success=True)
        path = write_export_log(tmp_path, [result], total_emails=3, filters=filters)
        data = json.loads(path.read_text())

        assert data["filters_applied"]["date_from"] == "2024-01-01"
        assert data["filters_applied"]["date_to"] == "2024-12-31"
        assert data["filters_applied"]["sender"] == "alice@aol.com"
        assert data["filters_applied"]["subject"] == "invoice"

    def test_log_records_errors(self, tmp_path):
        result = ExportResult(
            format_name="pdf",
            file_path="/tmp/test.pdf",
            record_count=0,
            success=False,
            error="Font encoding failed",
            warnings=["Unicode replacement in 3 emails"],
        )
        path = write_export_log(tmp_path, [result], total_emails=10)
        data = json.loads(path.read_text())

        assert data["success"] is False
        export = data["exports"][0]
        assert export["error"] == "Font encoding failed"
        assert "Unicode replacement" in export["warnings"][0]

    def test_log_empty_filters_omitted(self, tmp_path):
        result = ExportResult(format_name="csv", file_path="/tmp/test.csv.gz", record_count=0, success=True)
        path = write_export_log(tmp_path, [result], total_emails=0, filters=FilterParams())
        data = json.loads(path.read_text())
        assert data["filters_applied"] == {}
