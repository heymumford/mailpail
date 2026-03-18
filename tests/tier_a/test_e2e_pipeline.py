# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier A — End-to-end pipeline tests against a real IMAP server (pymap).

No mocks. The real IMAPClient, real imap_tools, real filters, real exporters,
real manifest, real zip — everything runs for real against pymap's in-memory
dict backend.

If these pass, the product works. If these fail, users see bugs.
"""

from __future__ import annotations

import csv
import email.utils
import gzip
import imaplib
import json
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import pytest

from mailpail.client import IMAPClient
from mailpail.exporters import get_exporter
from mailpail.exporters.export_log import write_export_log
from mailpail.exporters.incremental import filter_new_records, save_exported_uids
from mailpail.exporters.manifest import write_manifest
from mailpail.exporters.zipper import zip_export
from mailpail.filters import apply_filters
from mailpail.models import ExportConfig, FilterParams

pytestmark = [pytest.mark.tier_a, pytest.mark.e2e]

_PYMAP_PORT = 14199
_USER = "demouser"
_PASS = "demopass"


def _build_email(
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    date: datetime | None = None,
    attachments: list[tuple[str, bytes]] | None = None,
) -> bytes:
    """Build an RFC 822 message."""
    if attachments:
        msg = EmailMessage()
        msg.make_mixed()
        text_part = EmailMessage()
        text_part.set_content(body)
        msg.attach(text_part)
        for name, data in attachments:
            msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=name)
    else:
        msg = EmailMessage()
        msg.set_content(body)

    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    dt = date or datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
    msg["Date"] = email.utils.format_datetime(dt)
    return msg.as_bytes()


@pytest.fixture(scope="module")
def imap_server():
    """Start pymap with in-memory dict backend, pre-populate with test emails."""
    proc = subprocess.Popen(
        ["uv", "run", "pymap", "--port", str(_PYMAP_PORT), "--no-tls", "dict", "--demo-data"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)

    # Pre-populate via raw IMAP APPEND
    conn = imaplib.IMAP4("localhost", _PYMAP_PORT)
    conn.login(_USER, _PASS)

    # Create folders (some may already exist from demo-data)
    for folder in ["Sent", "Draft", "Trash", '"Bulk Mail"']:
        try:
            conn.create(folder)
        except Exception:
            pass  # folder already exists

    # 5 INBOX messages
    emails = [
        (
            "alice@aol.com",
            "testuser@test.com",
            "Happy Birthday!",
            "Many happy returns!",
            datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc),
            None,
        ),
        (
            "bob@yahoo.com",
            "testuser@test.com",
            "Invoice #2024-001",
            "Please find your invoice attached.",
            datetime(2024, 6, 5, 14, 0, tzinfo=timezone.utc),
            [("invoice.pdf", b"%PDF-fake-invoice")],
        ),
        (
            "carol@gmail.com",
            "testuser@test.com",
            "Vacation photos",
            "Here are the pics!",
            datetime(2024, 7, 10, 9, 0, tzinfo=timezone.utc),
            [("beach.jpg", b"\xff\xd8-fake-jpg"), ("sunset.jpg", b"\xff\xd8-fake-jpg-2")],
        ),
        (
            "alice@aol.com",
            "testuser@test.com",
            "Re: Dinner plans",
            "7pm works for me!",
            datetime(2024, 8, 1, 18, 0, tzinfo=timezone.utc),
            None,
        ),
        (
            "noreply@amazon.com",
            "testuser@test.com",
            "Your order shipped",
            "Tracking: 1Z999",
            datetime(2024, 8, 15, 8, 0, tzinfo=timezone.utc),
            None,
        ),
    ]
    for from_a, to_a, subj, body, dt, atts in emails:
        raw = _build_email(from_a, to_a, subj, body, dt, atts)
        conn.append("INBOX", "", imaplib.Time2Internaldate(dt.timestamp()), raw)

    # 2 Sent messages
    for from_a, to_a, subj, body, dt in [
        (
            "testuser@test.com",
            "alice@aol.com",
            "Re: Happy Birthday!",
            "Thank you!",
            datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
        ),
        (
            "testuser@test.com",
            "bob@yahoo.com",
            "Re: Invoice",
            "Received, thanks.",
            datetime(2024, 6, 6, 9, 0, tzinfo=timezone.utc),
        ),
    ]:
        raw = _build_email(from_a, to_a, subj, body, dt)
        conn.append("Sent", "", imaplib.Time2Internaldate(dt.timestamp()), raw)

    conn.logout()
    yield {"host": "localhost", "port": _PYMAP_PORT}

    proc.terminate()
    proc.wait(timeout=5)


def _client(srv: dict) -> IMAPClient:
    return IMAPClient(username=_USER, password=_PASS, server=srv["host"], port=srv["port"], use_ssl=False)


# -- E2E: Connect + List Folders ---------------------------------------------


class TestE2EConnection:
    def test_connect_and_disconnect(self, imap_server):
        c = _client(imap_server)
        c.connect()
        c.disconnect()

    def test_wrong_password_rejected(self, imap_server):
        c = IMAPClient(
            username=_USER, password="wrong", server=imap_server["host"], port=imap_server["port"], use_ssl=False
        )
        with pytest.raises(ConnectionError):
            c.connect()

    def test_list_folders(self, imap_server):
        with _client(imap_server) as c:
            folders = c.list_folders()
        assert "INBOX" in folders
        assert "Sent" in folders
        assert "Draft" in folders
        assert "Bulk Mail" in folders


# -- E2E: Fetch + Filter -----------------------------------------------------


class TestE2EFetchAndFilter:
    def test_fetch_inbox(self, imap_server):
        with _client(imap_server) as c:
            records = c.fetch_emails(FilterParams(folder="INBOX"))
        assert len(records) >= 5
        subjects = {r.subject for r in records}
        assert "Happy Birthday!" in subjects
        assert "Invoice #2024-001" in subjects

    def test_fetch_preserves_attachments(self, imap_server):
        with _client(imap_server) as c:
            records = c.fetch_emails(FilterParams(folder="INBOX"))
        with_atts = [r for r in records if r.has_attachments]
        assert len(with_atts) >= 2  # invoice + vacation photos

    def test_filter_by_sender(self, imap_server):
        with _client(imap_server) as c:
            records = c.fetch_emails(FilterParams(folder="INBOX"))
        filtered = apply_filters(records, FilterParams(sender="alice"))
        assert len(filtered) >= 2

    def test_filter_by_subject(self, imap_server):
        with _client(imap_server) as c:
            records = c.fetch_emails(FilterParams(folder="INBOX"))
        filtered = apply_filters(records, FilterParams(subject="invoice"))
        assert len(filtered) >= 1

    def test_fetch_sent_folder(self, imap_server):
        with _client(imap_server) as c:
            records = c.fetch_emails(FilterParams(folder="Sent"))
        assert len(records) >= 2


# -- E2E: Full Export Pipeline ------------------------------------------------


class TestE2EExportPipeline:
    def _fetch(self, imap_server):
        with _client(imap_server) as c:
            return c.fetch_emails(FilterParams(folder="INBOX"))

    def test_csv_export(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("csv").export(records, config)
        assert result.success
        assert result.record_count >= 5
        with gzip.open(result.file_path, "rt", newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 5
        assert all(r["sender"] for r in rows)

    def test_excel_export(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("excel").export(records, config)
        assert result.success and Path(result.file_path).exists()

    def test_pdf_export(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("pdf").export(records, config)
        assert result.success and Path(result.file_path).exists()

    def test_mbox_export(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("mbox").export(records, config)
        assert result.success and Path(result.file_path).exists()

    def test_eml_export(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("eml").export(records, config)
        assert result.success

    def test_attachments_saved_to_disk(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("csv").export(records, config)
        assert result.success
        att_dir = tmp_path / "attachments"
        assert att_dir.is_dir()
        assert len(list(att_dir.iterdir())) >= 2

    def test_manifest_has_sha256(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("csv").export(records, config)
        manifest_path = write_manifest(tmp_path, [result], total_emails=len(records))
        data = json.loads(manifest_path.read_text())
        assert data["total_emails"] >= 5
        assert len(data["exports"][0]["sha256"]) == 64

    def test_zip_contains_everything(self, imap_server, tmp_path):
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(export_dir), filename_prefix="e2e")
        get_exporter("csv").export(records, config)
        write_manifest(export_dir, [], total_emails=len(records))
        zip_path = zip_export(export_dir)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        assert "e2e.csv.gz" in names
        assert "manifest.json" in names

    def test_export_log(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        config = ExportConfig(output_dir=str(tmp_path), filename_prefix="e2e")
        result = get_exporter("csv").export(records, config)
        log_path = write_export_log(tmp_path, [result], len(records), folders=["INBOX"])
        data = json.loads(log_path.read_text())
        assert data["total_emails_matched"] >= 5

    def test_incremental_skips_second_run(self, imap_server, tmp_path):
        records = self._fetch(imap_server)
        new1 = filter_new_records(records, tmp_path)
        assert len(new1) == len(records)  # first run: all are new
        save_exported_uids(tmp_path, {r.uid for r in new1})
        new2 = filter_new_records(records, tmp_path)
        assert len(new2) == 0  # second run: all skipped
