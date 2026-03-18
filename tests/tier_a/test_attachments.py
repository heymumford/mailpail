# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime

import pytest

from mailpail.exporters.attachments import attachment_filenames, save_attachments
from mailpail.models import Attachment, EmailRecord

pytestmark = pytest.mark.tier_a


def _make_att(name: str = "report.pdf", content: bytes = b"fake-pdf-content") -> Attachment:
    return Attachment(
        filename=name,
        content_type="application/pdf",
        payload=content,
        size=len(content),
    )


def _make_record_with_atts(uid: str, attachments: tuple[Attachment, ...]) -> EmailRecord:
    return EmailRecord(
        uid=uid,
        date=datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.UTC),
        sender="sender@test.com",
        to="me@test.com",
        cc="",
        subject=f"Email {uid}",
        body_text="Body text",
        body_html="",
        folder="INBOX",
        has_attachments=bool(attachments),
        message_id=f"<{uid}@test>",
        attachments=attachments,
    )


class TestAttachmentFilenames:
    def test_empty_attachments(self):
        rec = _make_record_with_atts("1", ())
        assert attachment_filenames(rec) == ""

    def test_single_attachment(self):
        rec = _make_record_with_atts("1", (_make_att("report.pdf"),))
        assert attachment_filenames(rec) == "report.pdf"

    def test_multiple_attachments(self):
        rec = _make_record_with_atts(
            "1",
            (_make_att("report.pdf"), _make_att("photo.jpg")),
        )
        assert attachment_filenames(rec) == "report.pdf; photo.jpg"


class TestSaveAttachments:
    def test_saves_files_to_disk(self, tmp_path):
        att = _make_att("report.pdf", b"pdf-content-here")
        rec = _make_record_with_atts("1", (att,))
        count = save_attachments([rec], tmp_path)
        assert count == 1
        att_dir = tmp_path / "attachments"
        assert att_dir.is_dir()
        files = list(att_dir.iterdir())
        assert len(files) == 1
        assert files[0].read_bytes() == b"pdf-content-here"

    def test_saves_multiple_attachments(self, tmp_path):
        atts = (_make_att("a.txt", b"aaa"), _make_att("b.txt", b"bbb"))
        rec = _make_record_with_atts("1", atts)
        count = save_attachments([rec], tmp_path)
        assert count == 2

    def test_no_attachments_returns_zero(self, tmp_path):
        rec = _make_record_with_atts("1", ())
        count = save_attachments([rec], tmp_path)
        assert count == 0
        assert not (tmp_path / "attachments").exists()

    def test_multiple_records(self, tmp_path):
        rec1 = _make_record_with_atts("1", (_make_att("a.txt", b"aaa"),))
        rec2 = _make_record_with_atts("2", (_make_att("b.txt", b"bbb"),))
        rec3 = _make_record_with_atts("3", ())
        count = save_attachments([rec1, rec2, rec3], tmp_path)
        assert count == 2
        files = list((tmp_path / "attachments").iterdir())
        assert len(files) == 2

    def test_filename_prefixed_with_uid(self, tmp_path):
        att = _make_att("report.pdf", b"content")
        rec = _make_record_with_atts("42", (att,))
        save_attachments([rec], tmp_path)
        files = list((tmp_path / "attachments").iterdir())
        assert any("42" in f.name for f in files)
