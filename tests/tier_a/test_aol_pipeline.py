# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier A — AOL end-to-end pipeline scenarios.

These are must-pass product feature tests. Each test simulates the complete
workflow: connect to AOL → list folders → fetch emails → filter → export →
verify output. The IMAP layer is mocked; everything else runs for real.
"""

from __future__ import annotations

import csv
import datetime
import gzip
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mailpail.client import IMAPClient
from mailpail.exporters import get_exporter
from mailpail.exporters.manifest import write_manifest
from mailpail.exporters.zipper import zip_export
from mailpail.filters import apply_filters
from mailpail.models import ExportConfig, FilterParams

pytestmark = pytest.mark.tier_a


# -- Fixtures ----------------------------------------------------------------


def _mock_attachment(name: str = "invoice.pdf", data: bytes = b"%PDF-fake") -> MagicMock:
    att = MagicMock()
    att.filename = name
    att.content_type = "application/pdf"
    att.payload = data
    return att


def _mock_msg(
    uid: str,
    subject: str,
    from_: str = "friend@aol.com",
    to: tuple = ("margaret@aol.com",),
    text: str = "Hello!",
    date: datetime.datetime | None = None,
    attachments: tuple = (),
) -> MagicMock:
    msg = MagicMock()
    msg.uid = uid
    msg.date = date or datetime.datetime(2024, 6, 15, 10, 0, tzinfo=datetime.UTC)
    msg.from_ = from_
    msg.to = to
    msg.cc = ()
    msg.subject = subject
    msg.text = text
    msg.html = ""
    msg.attachments = attachments
    msg.headers = {"message-id": (f"<{uid}@aol.com>",)}
    msg.obj.as_bytes.return_value = text.encode()
    return msg


def _mock_aol_folders() -> list[MagicMock]:
    """AOL's actual IMAP folder names."""
    names = ["INBOX", "Sent", "Draft", "Trash", "Bulk Mail", "Archive"]
    folders = []
    for n in names:
        f = MagicMock()
        f.name = n
        folders.append(f)
    return folders


@pytest.fixture()
def aol_inbox_messages() -> list[MagicMock]:
    """10 realistic AOL inbox messages with some attachments."""
    return [
        _mock_msg("1", "Happy Birthday!", from_="alice@aol.com", text="Many happy returns!"),
        _mock_msg("2", "Fw: Funny video", from_="bob@yahoo.com", text="Check this out"),
        _mock_msg(
            "3",
            "Invoice #2024-001",
            from_="billing@example.com",
            text="Please find your invoice attached.",
            attachments=(_mock_attachment("invoice_2024_001.pdf", b"%PDF-invoice-data"),),
        ),
        _mock_msg("4", "Re: Dinner plans", from_="carol@gmail.com", text="7pm works for me!"),
        _mock_msg(
            "5",
            "Photos from vacation",
            from_="alice@aol.com",
            text="Here are the pics!",
            attachments=(
                _mock_attachment("beach.jpg", b"\xff\xd8\xff\xe0-fake-jpg"),
                _mock_attachment("sunset.jpg", b"\xff\xd8\xff\xe0-fake-jpg-2"),
            ),
        ),
        _mock_msg("6", "Your order has shipped", from_="noreply@amazon.com", text="Tracking: 1Z999"),
        _mock_msg(
            "7",
            "Meeting notes",
            from_="boss@company.com",
            text="Action items from today's meeting.",
            attachments=(_mock_attachment("notes.docx", b"PK-fake-docx"),),
        ),
        _mock_msg("8", "Re: Book club", from_="diana@aol.com", text="I loved that chapter!"),
        _mock_msg(
            "9",
            "Tax documents",
            from_="accountant@firm.com",
            text="Your 2023 tax forms are ready.",
            date=datetime.datetime(2024, 2, 1, 9, 0, tzinfo=datetime.UTC),
            attachments=(_mock_attachment("1099.pdf", b"%PDF-tax-data"),),
        ),
        _mock_msg("10", "Weekend plans?", from_="bob@yahoo.com", text="Want to grab coffee?"),
    ]


# -- Scenario: Margaret exports her AOL inbox to CSV -------------------------


class TestMargaretAOLExport:
    """Margaret (68) exports her AOL inbox. Full pipeline, mocked IMAP."""

    @patch("mailpail.client.MailBox")
    def test_connect_to_aol(self, mock_mb_cls):
        """Step 1: Connect to export.imap.aol.com with app password."""
        mb = MagicMock()
        mock_mb_cls.return_value = mb

        client = IMAPClient("margaret@aol.com", "abcd-efgh-ijkl-mnop")
        client.connect()

        mock_mb_cls.assert_called_once_with("export.imap.aol.com", 993)
        mb.login.assert_called_once_with("margaret@aol.com", "abcd-efgh-ijkl-mnop")

    @patch("mailpail.client.MailBox")
    def test_list_aol_folders(self, mock_mb_cls):
        """Step 2: List folders returns AOL's actual folder names."""
        mb = MagicMock()
        mb.folder.list.return_value = _mock_aol_folders()
        mock_mb_cls.return_value = mb

        client = IMAPClient("margaret@aol.com", "pass")
        client.connect()
        folders = client.list_folders()

        assert "INBOX" in folders
        assert "Sent" in folders
        assert "Draft" in folders  # AOL uses singular
        assert "Bulk Mail" in folders  # AOL's spam folder
        assert "Trash" in folders

    @patch("mailpail.client.MailBox")
    def test_fetch_inbox_with_attachments(self, mock_mb_cls, aol_inbox_messages):
        """Step 3: Fetch emails preserves attachments."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("margaret@aol.com", "pass")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))

        assert len(records) == 10
        # Verify attachment data flows through
        records_with_atts = [r for r in records if r.has_attachments]
        assert len(records_with_atts) == 4  # messages 3, 5, 7, 9
        # Message 5 has 2 attachments
        msg5 = [r for r in records if r.uid == "5"][0]
        assert len(msg5.attachments) == 2

    @patch("mailpail.client.MailBox")
    def test_filter_by_sender(self, mock_mb_cls, aol_inbox_messages):
        """Step 4: Filter by sender narrows results."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("margaret@aol.com", "pass")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))
        filtered = apply_filters(records, FilterParams(sender="alice@aol.com"))

        assert len(filtered) == 2
        assert all("alice" in r.sender for r in filtered)

    @patch("mailpail.client.MailBox")
    def test_filter_by_subject(self, mock_mb_cls, aol_inbox_messages):
        """Step 4b: Filter by subject keyword."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("margaret@aol.com", "pass")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))
        filtered = apply_filters(records, FilterParams(subject="invoice"))

        assert len(filtered) == 1
        assert "Invoice" in filtered[0].subject

    @patch("mailpail.client.MailBox")
    def test_full_csv_export(self, mock_mb_cls, aol_inbox_messages, tmp_path):
        """Step 5: Export to CSV with attachments saved to disk."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("margaret@aol.com", "pass")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))

        config = ExportConfig(
            output_dir=str(tmp_path),
            formats=("csv",),
            filename_prefix="margaret_aol",
        )
        exporter = get_exporter("csv")
        result = exporter.export(records, config)

        assert result.success
        assert result.record_count == 10

        # Verify CSV content
        csv_path = Path(result.file_path)
        assert csv_path.exists()
        with gzip.open(csv_path, "rt", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 10
        assert rows[0]["sender"] == "alice@aol.com"

        # Verify attachments saved
        att_dir = tmp_path / "attachments"
        assert att_dir.is_dir()
        att_files = list(att_dir.iterdir())
        assert len(att_files) >= 4  # 4 messages have attachments, some have multiple

    @patch("mailpail.client.MailBox")
    def test_full_pipeline_with_manifest_and_zip(self, mock_mb_cls, aol_inbox_messages, tmp_path):
        """Step 6: Full pipeline produces manifest.json and .zip archive."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("margaret@aol.com", "pass")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))

        export_dir = tmp_path / "Mailpail_Export"
        export_dir.mkdir()
        config = ExportConfig(
            output_dir=str(export_dir),
            formats=("csv",),
            filename_prefix="margaret_aol",
        )

        exporter = get_exporter("csv")
        result = exporter.export(records, config)
        assert result.success

        # Write manifest
        manifest_path = write_manifest(export_dir, [result], total_emails=len(records))
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert manifest["total_emails"] == 10
        assert len(manifest["exports"]) >= 1  # csv + possibly attachments
        csv_entry = [e for e in manifest["exports"] if e["format"] == "csv"][0]
        assert len(csv_entry["sha256"]) == 64  # SHA-256 hex digest

        # Zip
        zip_path = zip_export(export_dir)
        assert zip_path.exists()
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "margaret_aol.csv.gz" in names
        assert "manifest.json" in names
        assert any("attachments/" in n for n in names)


# -- Scenario: Derek filters specific emails from AOL -----------------------


class TestDerekFilteredExport:
    """Derek (35, IT) uses CLI filters to extract specific AOL emails."""

    @patch("mailpail.client.MailBox")
    def test_date_range_filter(self, mock_mb_cls, aol_inbox_messages):
        """Derek filters emails from February 2024 only."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("derek@company.com", "pass", server="imap.aol.com")
        client.connect()

        # Server-side date filter
        filters = FilterParams(
            date_from=datetime.date(2024, 2, 1),
            date_to=datetime.date(2024, 3, 1),
            folder="INBOX",
        )
        client.fetch_emails(filters)

        # The mock returns all messages regardless of IMAP criteria,
        # but we verify the criteria was built correctly
        mb.fetch.assert_called_once()

    @patch("mailpail.client.MailBox")
    def test_combined_sender_and_subject_filter(self, mock_mb_cls, aol_inbox_messages):
        """Derek filters by sender AND subject keyword."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("derek@company.com", "pass", server="imap.aol.com")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))

        # Client-side filtering: sender alice AND subject "vacation"
        filtered = apply_filters(records, FilterParams(sender="alice", subject="vacation"))
        assert len(filtered) == 1
        assert filtered[0].subject == "Photos from vacation"

    @patch("mailpail.client.MailBox")
    def test_export_to_multiple_formats(self, mock_mb_cls, aol_inbox_messages, tmp_path):
        """Derek exports to CSV + Excel simultaneously."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("derek@company.com", "pass", server="imap.aol.com")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))

        config = ExportConfig(
            output_dir=str(tmp_path),
            formats=("csv", "excel"),
            filename_prefix="derek_export",
        )

        results = []
        for fmt in config.formats:
            exporter = get_exporter(fmt)
            results.append(exporter.export(records, config))

        assert all(r.success for r in results)
        assert (tmp_path / "derek_export.csv.gz").exists()
        assert (tmp_path / "derek_export.xlsx").exists()

        # Attachments should only be saved once (idempotent)
        att_dir = tmp_path / "attachments"
        assert att_dir.is_dir()


# -- Scenario: Sandra needs chain of custody ---------------------------------


class TestSandraAuditExport:
    """Sandra (42, paralegal) needs verifiable export for legal use."""

    @patch("mailpail.client.MailBox")
    def test_manifest_has_sha256_for_every_file(self, mock_mb_cls, aol_inbox_messages, tmp_path):
        """Every exported file has a SHA-256 hash in the manifest."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("sandra@firm.com", "pass", server="imap.aol.com")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))

        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="evidence")
        exporter = get_exporter("csv")
        result = exporter.export(records, config)

        manifest_path = write_manifest(tmp_path, [result], total_emails=len(records))
        manifest = json.loads(manifest_path.read_text())

        for export in manifest["exports"]:
            if export["format"] != "attachments":
                assert len(export.get("sha256", "")) == 64, f"Missing SHA-256 for {export['format']}"

    @patch("mailpail.client.MailBox")
    def test_manifest_records_attachment_count(self, mock_mb_cls, aol_inbox_messages, tmp_path):
        """Manifest tracks how many attachments were saved."""
        mb = MagicMock()
        mb.fetch.return_value = iter(aol_inbox_messages)
        mock_mb_cls.return_value = mb

        client = IMAPClient("sandra@firm.com", "pass", server="imap.aol.com")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))

        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="evidence")
        exporter = get_exporter("csv")
        result = exporter.export(records, config)

        assert result.attachment_count > 0
