# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import zipfile

import pytest

from mailpail.exporters.zipper import zip_export

pytestmark = pytest.mark.tier_a


class TestZipper:
    def test_creates_zip_file(self, tmp_path):
        export_dir = tmp_path / "Mailpail_Export"
        export_dir.mkdir()
        (export_dir / "test.csv.gz").write_bytes(b"fake-csv")
        (export_dir / "manifest.json").write_text('{"test": true}')

        zip_path = zip_export(export_dir)
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        assert zip_path.parent == tmp_path  # zip is alongside, not inside

    def test_zip_contains_all_files(self, tmp_path):
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        (export_dir / "data.csv.gz").write_bytes(b"csv-content")
        (export_dir / "manifest.json").write_text("{}")

        att_dir = export_dir / "attachments"
        att_dir.mkdir()
        (att_dir / "1_report.pdf").write_bytes(b"pdf-content")

        zip_path = zip_export(export_dir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = set(zf.namelist())
        assert "data.csv.gz" in names
        assert "manifest.json" in names
        assert "attachments/1_report.pdf" in names

    def test_zip_is_deflated(self, tmp_path):
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        (export_dir / "data.txt").write_text("hello " * 1000)

        zip_path = zip_export(export_dir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            info = zf.infolist()[0]
        assert info.compress_type == zipfile.ZIP_DEFLATED

    def test_custom_zip_name(self, tmp_path):
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        (export_dir / "file.txt").write_bytes(b"content")

        zip_path = zip_export(export_dir, zip_name="custom_archive.zip")
        assert zip_path.name == "custom_archive.zip"
        assert zip_path.exists()

    def test_empty_directory(self, tmp_path):
        export_dir = tmp_path / "empty"
        export_dir.mkdir()

        zip_path = zip_export(export_dir)
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, "r") as zf:
            assert len(zf.namelist()) == 0
