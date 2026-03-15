# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

pytestmark = pytest.mark.tier_a


def _get_parser():
    from aol_email_exporter.__main__ import _build_parser

    return _build_parser()


class TestCLI:
    def test_parse_minimal_args(self):
        parser = _get_parser()
        args = parser.parse_args(["--username", "user@aol.com"])
        assert args.username == "user@aol.com"
        assert args.format == ["csv"]
        assert args.dry_run is False
        assert args.list_folders is False

    def test_parse_all_args(self):
        parser = _get_parser()
        args = parser.parse_args(
            [
                "--cli",
                "--username",
                "user@aol.com",
                "--password",
                "secret",
                "--format",
                "csv",
                "excel",
                "pdf",
                "--output-dir",
                "/tmp/export",
                "--date-from",
                "2024-01-01",
                "--date-to",
                "2024-06-01",
                "--sender",
                "alice@aol.com",
                "--subject",
                "invoice",
                "--folder",
                "INBOX",
                "--group-by",
                "sender",
                "--prefix",
                "my_export",
                "--log-level",
                "DEBUG",
                "--log-file",
                "/tmp/export.log",
                "--dry-run",
                "--list-folders",
            ]
        )
        assert args.username == "user@aol.com"
        assert args.password == "secret"
        assert args.format == ["csv", "excel", "pdf"]
        assert args.output_dir == "/tmp/export"
        assert args.date_from == "2024-01-01"
        assert args.date_to == "2024-06-01"
        assert args.sender == "alice@aol.com"
        assert args.subject == "invoice"
        assert args.folder == "INBOX"
        assert args.group_by == "sender"
        assert args.prefix == "my_export"
        assert args.log_level == "DEBUG"
        assert args.log_file == "/tmp/export.log"
        assert args.dry_run is True
        assert args.list_folders is True

    def test_format_choices(self):
        parser = _get_parser()
        for fmt in ("csv", "excel", "excel-sheets", "pdf"):
            args = parser.parse_args(["--username", "u@aol.com", "--format", fmt])
            assert fmt in args.format

    def test_invalid_format_rejected(self):
        parser = _get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--username", "u@aol.com", "--format", "docx"])

    def test_list_folders_flag(self):
        parser = _get_parser()
        args = parser.parse_args(["--username", "u@aol.com", "--list-folders"])
        assert args.list_folders is True

    def test_dry_run_flag(self):
        parser = _get_parser()
        args = parser.parse_args(["--username", "u@aol.com", "--dry-run"])
        assert args.dry_run is True
