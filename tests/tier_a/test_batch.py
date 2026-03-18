# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from mailpail.batch import BatchEntry, load_batch_file

pytestmark = pytest.mark.tier_a


class TestBatchFileLoading:
    def test_load_simple_csv(self, tmp_path):
        csv_file = tmp_path / "accounts.csv"
        csv_file.write_text("username,password\nmargaret@aol.com,abcd-efgh\nderek@gmail.com,wxyz-1234\n")

        entries = load_batch_file(csv_file)
        assert len(entries) == 2
        assert entries[0].username == "margaret@aol.com"
        assert entries[0].password == "abcd-efgh"
        assert entries[0].provider == "aol"  # default
        assert entries[1].username == "derek@gmail.com"

    def test_load_full_csv(self, tmp_path):
        csv_file = tmp_path / "accounts.csv"
        csv_file.write_text(
            "username,password,provider,folder,format\n"
            "user@aol.com,pass1,aol,INBOX,csv\n"
            "user@gmail.com,pass2,gmail,Sent,excel\n"
        )
        entries = load_batch_file(csv_file)
        assert len(entries) == 2
        assert entries[0].provider == "aol"
        assert entries[0].folder == "INBOX"
        assert entries[0].format == "csv"
        assert entries[1].provider == "gmail"
        assert entries[1].folder == "Sent"
        assert entries[1].format == "excel"

    def test_skips_empty_rows(self, tmp_path):
        csv_file = tmp_path / "accounts.csv"
        csv_file.write_text("username,password\nvalid@aol.com,pass\n,\n  ,  \n")

        entries = load_batch_file(csv_file)
        assert len(entries) == 1

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_batch_file(tmp_path / "nonexistent.csv")

    def test_raises_on_missing_columns(self, tmp_path):
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("email,pass\nuser@aol.com,secret\n")

        with pytest.raises(ValueError, match="username"):
            load_batch_file(csv_file)

    def test_raises_on_empty_file(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        with pytest.raises(ValueError, match="empty"):
            load_batch_file(csv_file)

    def test_defaults_applied(self, tmp_path):
        csv_file = tmp_path / "minimal.csv"
        csv_file.write_text("username,password\nuser@aol.com,pass\n")

        entries = load_batch_file(csv_file)
        assert entries[0].provider == "aol"
        assert entries[0].folder == "INBOX"
        assert entries[0].format == "csv"

    def test_case_insensitive_headers(self, tmp_path):
        csv_file = tmp_path / "caps.csv"
        csv_file.write_text("Username,Password,Provider\nuser@aol.com,pass,gmail\n")

        entries = load_batch_file(csv_file)
        assert len(entries) == 1
        assert entries[0].username == "user@aol.com"
        assert entries[0].provider == "gmail"

    def test_batch_entry_frozen(self):
        entry = BatchEntry(username="u", password="p")
        with pytest.raises(AttributeError):
            entry.username = "changed"  # type: ignore[misc]
