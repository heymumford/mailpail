# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime

import pytest

from mailpail.exporters.incremental import (
    filter_new_records,
    load_exported_uids,
    save_exported_uids,
)
from mailpail.models import EmailRecord

pytestmark = pytest.mark.tier_a


def _rec(uid: str) -> EmailRecord:
    return EmailRecord(
        uid=uid,
        date=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
        sender="a@b.com",
        to="c@d.com",
        cc="",
        subject=f"Email {uid}",
        body_text="body",
        body_html="",
        folder="INBOX",
        has_attachments=False,
        message_id=f"<{uid}@test>",
    )


class TestLoadExportedUIDs:
    def test_empty_when_no_state_file(self, tmp_path):
        assert load_exported_uids(tmp_path) == set()

    def test_loads_uids_from_file(self, tmp_path):
        (tmp_path / ".mailpail_exported").write_text("uid1\nuid2\nuid3\n")
        assert load_exported_uids(tmp_path) == {"uid1", "uid2", "uid3"}

    def test_ignores_blank_lines(self, tmp_path):
        (tmp_path / ".mailpail_exported").write_text("uid1\n\n\nuid2\n")
        assert load_exported_uids(tmp_path) == {"uid1", "uid2"}


class TestSaveExportedUIDs:
    def test_saves_uids(self, tmp_path):
        save_exported_uids(tmp_path, {"a", "b", "c"})
        content = (tmp_path / ".mailpail_exported").read_text()
        assert "a" in content
        assert "b" in content
        assert "c" in content

    def test_appends_new_uids(self, tmp_path):
        save_exported_uids(tmp_path, {"a", "b"})
        save_exported_uids(tmp_path, {"b", "c"})
        uids = load_exported_uids(tmp_path)
        assert uids == {"a", "b", "c"}

    def test_idempotent(self, tmp_path):
        save_exported_uids(tmp_path, {"a"})
        save_exported_uids(tmp_path, {"a"})
        content = (tmp_path / ".mailpail_exported").read_text()
        assert content.strip().count("a") == 1


class TestFilterNewRecords:
    def test_all_new_when_no_state(self, tmp_path):
        records = [_rec("1"), _rec("2"), _rec("3")]
        result = filter_new_records(records, tmp_path)
        assert len(result) == 3

    def test_skips_already_exported(self, tmp_path):
        save_exported_uids(tmp_path, {"1", "2"})
        records = [_rec("1"), _rec("2"), _rec("3"), _rec("4")]
        result = filter_new_records(records, tmp_path)
        assert len(result) == 2
        assert {r.uid for r in result} == {"3", "4"}

    def test_all_skipped(self, tmp_path):
        save_exported_uids(tmp_path, {"1", "2"})
        records = [_rec("1"), _rec("2")]
        result = filter_new_records(records, tmp_path)
        assert len(result) == 0

    def test_roundtrip_scenario(self, tmp_path):
        """Simulate two export runs — second run should skip the first batch."""
        batch1 = [_rec("1"), _rec("2"), _rec("3")]
        result1 = filter_new_records(batch1, tmp_path)
        assert len(result1) == 3
        save_exported_uids(tmp_path, {r.uid for r in result1})

        batch2 = [_rec("1"), _rec("2"), _rec("3"), _rec("4"), _rec("5")]
        result2 = filter_new_records(batch2, tmp_path)
        assert len(result2) == 2
        assert {r.uid for r in result2} == {"4", "5"}
