# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime

import pytest

from aol_email_exporter.models import EmailRecord, ExportConfig


def _make_record(
    uid: str,
    date: datetime.datetime,
    sender: str,
    to: str,
    subject: str,
    body_text: str,
    folder: str,
    *,
    cc: str = "",
    body_html: str = "",
    has_attachments: bool = False,
    message_id: str = "",
    size_bytes: int = 0,
) -> EmailRecord:
    return EmailRecord(
        uid=uid,
        date=date,
        sender=sender,
        to=to,
        cc=cc,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        folder=folder,
        has_attachments=has_attachments,
        message_id=message_id or f"<{uid}@aol.com>",
        size_bytes=size_bytes,
    )


@pytest.fixture(scope="session")
def sample_records() -> list[EmailRecord]:
    """Ten diverse EmailRecord objects spanning 2023-01 to 2024-06."""
    return [
        _make_record(
            uid="1",
            date=datetime.datetime(2023, 1, 15, 8, 30, tzinfo=datetime.UTC),
            sender="alice@aol.com",
            to="me@aol.com",
            subject="January newsletter",
            body_text="Happy new year! Here is the latest news.",
            folder="INBOX",
            size_bytes=1024,
        ),
        _make_record(
            uid="2",
            date=datetime.datetime(2023, 3, 22, 14, 0, tzinfo=datetime.UTC),
            sender="bob@example.com",
            to="me@aol.com",
            subject="Invoice #2023-100",
            body_text="Please find attached the invoice for March.",
            folder="INBOX",
            has_attachments=True,
            size_bytes=5120,
        ),
        _make_record(
            uid="3",
            date=datetime.datetime(2023, 5, 1, 9, 15, tzinfo=datetime.UTC),
            sender="alice@aol.com",
            to="bob@example.com",
            subject="Re: Project update",
            body_text="Thanks for the update, looks good.",
            folder="Sent",
            size_bytes=512,
        ),
        _make_record(
            uid="4",
            date=datetime.datetime(2023, 7, 4, 12, 0, tzinfo=datetime.UTC),
            sender="carol@domain.org",
            to="me@aol.com",
            subject="Fourth of July sale!",
            body_text="Big savings this weekend only.",
            body_html="<h1>Big savings</h1><p>This weekend only.</p>",
            folder="INBOX",
            size_bytes=2048,
        ),
        _make_record(
            uid="5",
            date=datetime.datetime(2023, 9, 10, 7, 45, tzinfo=datetime.UTC),
            sender="bob@example.com",
            to="me@aol.com",
            subject="Meeting notes Sept 9",
            body_text="Attached are the notes from yesterday's meeting.",
            folder="Archive",
            has_attachments=True,
            size_bytes=10240,
        ),
        _make_record(
            uid="6",
            date=datetime.datetime(2023, 11, 28, 16, 30, tzinfo=datetime.UTC),
            sender="alice@aol.com",
            to="me@aol.com",
            subject="Thanksgiving photos",
            body_text="Here are the photos from dinner.",
            folder="INBOX",
            has_attachments=True,
            size_bytes=20480,
        ),
        _make_record(
            uid="7",
            date=datetime.datetime(2024, 1, 5, 10, 0, tzinfo=datetime.UTC),
            sender="carol@domain.org",
            to="me@aol.com",
            subject="New year check-in",
            body_text="How are things going? Let's catch up.",
            folder="INBOX",
            size_bytes=768,
        ),
        _make_record(
            uid="8",
            date=datetime.datetime(2024, 2, 14, 8, 0, tzinfo=datetime.UTC),
            sender="bob@example.com",
            to="me@aol.com, alice@aol.com",
            cc="carol@domain.org",
            subject="Valentine's plans",
            body_text="Dinner reservation confirmed for 7 PM.",
            folder="Sent",
            size_bytes=640,
        ),
        _make_record(
            uid="9",
            date=datetime.datetime(2024, 4, 20, 11, 30, tzinfo=datetime.UTC),
            sender="alice@aol.com",
            to="me@aol.com",
            subject="Spring cleaning tips",
            body_text="A few ideas to declutter your inbox and home.",
            folder="Archive",
            size_bytes=1536,
        ),
        _make_record(
            uid="10",
            date=datetime.datetime(2024, 6, 1, 6, 0, tzinfo=datetime.UTC),
            sender="carol@domain.org",
            to="me@aol.com",
            subject="Summer plans?",
            body_text="Any vacation ideas for August?",
            folder="INBOX",
            size_bytes=384,
        ),
    ]


@pytest.fixture(scope="session")
def small_records() -> list[EmailRecord]:
    """Three minimal records for quick tests."""
    return [
        _make_record(
            uid="s1",
            date=datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.UTC),
            sender="alpha@aol.com",
            to="me@aol.com",
            subject="First",
            body_text="Body one.",
            folder="INBOX",
            size_bytes=100,
        ),
        _make_record(
            uid="s2",
            date=datetime.datetime(2024, 2, 1, 12, 0, tzinfo=datetime.UTC),
            sender="beta@aol.com",
            to="me@aol.com",
            subject="Second",
            body_text="Body two.",
            folder="Sent",
            size_bytes=200,
        ),
        _make_record(
            uid="s3",
            date=datetime.datetime(2024, 3, 1, 12, 0, tzinfo=datetime.UTC),
            sender="gamma@aol.com",
            to="me@aol.com",
            subject="Third",
            body_text="Body three.",
            folder="Archive",
            size_bytes=300,
        ),
    ]


@pytest.fixture(scope="session")
def empty_records() -> list[EmailRecord]:
    """Empty list for zero-record edge cases."""
    return []


@pytest.fixture()
def export_config(tmp_path) -> ExportConfig:
    """ExportConfig pointing at a unique tmp_path directory."""
    return ExportConfig(
        output_dir=str(tmp_path),
        formats=("csv", "excel", "pdf"),
        excel_group_by="folder",
        pdf_title="Test Export",
        filename_prefix="test_export",
    )
