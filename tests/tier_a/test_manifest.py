# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json

import pytest

from mailpail.exporters.manifest import write_manifest
from mailpail.models import ExportResult

pytestmark = pytest.mark.tier_a


class TestManifest:
    def test_creates_manifest_file(self, tmp_path):
        result = ExportResult(
            format_name="csv",
            file_path=str(tmp_path / "test.csv.gz"),
            record_count=10,
            success=True,
        )
        # Create a dummy file so stat works
        (tmp_path / "test.csv.gz").write_bytes(b"fake-gzip-content")

        path = write_manifest(tmp_path, [result], total_emails=10)
        assert path.exists()
        assert path.name == "manifest.json"

    def test_manifest_json_structure(self, tmp_path):
        (tmp_path / "test.csv.gz").write_bytes(b"fake-content")
        result = ExportResult(
            format_name="csv",
            file_path=str(tmp_path / "test.csv.gz"),
            record_count=5,
            success=True,
            attachment_count=2,
        )
        path = write_manifest(tmp_path, [result], total_emails=5)
        data = json.loads(path.read_text())

        assert "mailpail_version" in data
        assert "generated_utc" in data
        assert data["total_emails"] == 5
        assert len(data["exports"]) == 1
        export = data["exports"][0]
        assert export["format"] == "csv"
        assert export["record_count"] == 5
        assert export["attachment_count"] == 2
        assert "sha256" in export
        assert "size_bytes" in export

    def test_manifest_skips_failed_exports(self, tmp_path):
        result = ExportResult(
            format_name="csv",
            file_path=str(tmp_path / "test.csv.gz"),
            record_count=0,
            success=False,
            error="something broke",
        )
        path = write_manifest(tmp_path, [result], total_emails=0)
        data = json.loads(path.read_text())
        assert len(data["exports"]) == 0

    def test_manifest_includes_attachment_dir(self, tmp_path):
        att_dir = tmp_path / "attachments"
        att_dir.mkdir()
        (att_dir / "1_report.pdf").write_bytes(b"pdf-bytes")
        (att_dir / "2_image.jpg").write_bytes(b"jpg-bytes")

        path = write_manifest(tmp_path, [], total_emails=0)
        data = json.loads(path.read_text())
        att_entry = [e for e in data["exports"] if e["format"] == "attachments"]
        assert len(att_entry) == 1
        assert att_entry[0]["file_count"] == 2

    def test_manifest_multiple_exports(self, tmp_path):
        (tmp_path / "test.csv.gz").write_bytes(b"csv")
        (tmp_path / "test.xlsx").write_bytes(b"xlsx")

        results = [
            ExportResult(format_name="csv", file_path=str(tmp_path / "test.csv.gz"), record_count=10, success=True),
            ExportResult(format_name="excel", file_path=str(tmp_path / "test.xlsx"), record_count=10, success=True),
        ]
        path = write_manifest(tmp_path, results, total_emails=10)
        data = json.loads(path.read_text())
        assert len(data["exports"]) == 2
