# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from aol_email_exporter.client import AOLClient
from aol_email_exporter.models import FilterParams


pytestmark = pytest.mark.tier_a


def _mock_mailbox():
    """Return a MagicMock that behaves like imap_tools.MailBox."""
    mb = MagicMock()
    mb.login.return_value = None
    mb.logout.return_value = None
    mb.folder.list.return_value = []
    mb.folder.set.return_value = None
    mb.fetch.return_value = iter([])
    return mb


def _mock_message(
    uid: str = "1",
    date: datetime.datetime | None = None,
    from_: str = "sender@aol.com",
    to: tuple[str, ...] = ("me@aol.com",),
    cc: tuple[str, ...] = (),
    subject: str = "Test subject",
    text: str = "Test body",
    html: str = "",
    attachments: tuple = (),
    headers: dict | None = None,
) -> MagicMock:
    """Return a MagicMock that behaves like imap_tools.MailMessage."""
    msg = MagicMock()
    msg.uid = uid
    msg.date = date or datetime.datetime(2024, 1, 1, 12, 0, tzinfo=datetime.UTC)
    msg.from_ = from_
    msg.to = to
    msg.cc = cc
    msg.subject = subject
    msg.text = text
    msg.html = html
    msg.attachments = attachments
    msg.headers = headers or {}
    # obj.as_bytes() for size calculation
    msg.obj.as_bytes.return_value = b"x" * 256
    return msg


class TestAOLClient:
    """IMAP client wrapper tests using mocked MailBox."""

    @patch("aol_email_exporter.client.MailBox")
    def test_connect_success(self, mock_mailbox_cls):
        mb = _mock_mailbox()
        mock_mailbox_cls.return_value = mb

        client = AOLClient("user@aol.com", "apppassword123")
        client.connect()

        mock_mailbox_cls.assert_called_once_with("export.imap.aol.com", 993)
        mb.login.assert_called_once_with("user@aol.com", "apppassword123")

    @patch("aol_email_exporter.client.MailBox")
    def test_connect_failure(self, mock_mailbox_cls):
        mb = _mock_mailbox()
        mb.login.side_effect = Exception("Auth failed")
        mock_mailbox_cls.return_value = mb

        client = AOLClient("user@aol.com", "badpass")
        with pytest.raises(ConnectionError, match="Failed to connect"):
            client.connect()

    @patch("aol_email_exporter.client.MailBox")
    def test_context_manager(self, mock_mailbox_cls):
        mb = _mock_mailbox()
        mock_mailbox_cls.return_value = mb

        with AOLClient("user@aol.com", "pass") as client:
            mb.login.assert_called_once()
            assert client is not None
        mb.logout.assert_called_once()

    @patch("aol_email_exporter.client.MailBox")
    def test_list_folders(self, mock_mailbox_cls):
        mb = _mock_mailbox()
        folder1 = MagicMock()
        folder1.name = "INBOX"
        folder2 = MagicMock()
        folder2.name = "Sent"
        folder3 = MagicMock()
        folder3.name = "Trash"
        mb.folder.list.return_value = [folder1, folder2, folder3]
        mock_mailbox_cls.return_value = mb

        client = AOLClient("user@aol.com", "pass")
        client.connect()
        folders = client.list_folders()

        assert folders == ["INBOX", "Sent", "Trash"]

    @patch("aol_email_exporter.client.MailBox")
    def test_fetch_emails_basic(self, mock_mailbox_cls):
        mb = _mock_mailbox()
        msg = _mock_message(uid="42", subject="Hello world", from_="alice@aol.com")
        mb.fetch.return_value = iter([msg])
        mock_mailbox_cls.return_value = mb

        client = AOLClient("user@aol.com", "pass")
        client.connect()
        records = client.fetch_emails(FilterParams())

        assert len(records) == 1
        assert records[0].uid == "42"
        assert records[0].subject == "Hello world"
        assert records[0].sender == "alice@aol.com"
        assert records[0].folder == "INBOX"

    @patch("aol_email_exporter.client.AND")
    @patch("aol_email_exporter.client.MailBox")
    def test_fetch_with_date_filter(self, mock_mailbox_cls, mock_and):
        mb = _mock_mailbox()
        mock_mailbox_cls.return_value = mb
        mock_and.return_value = MagicMock()

        client = AOLClient("user@aol.com", "pass")
        client.connect()

        filters = FilterParams(
            date_from=datetime.date(2024, 1, 1),
            date_to=datetime.date(2024, 6, 1),
        )
        client.fetch_emails(filters)

        # Verify AND was called with date_gte and date_lt
        mock_and.assert_called_once()
        call_kwargs = mock_and.call_args[1]
        assert call_kwargs["date_gte"] == datetime.date(2024, 1, 1)
        assert call_kwargs["date_lt"] == datetime.date(2024, 6, 1)

    @patch("aol_email_exporter.client.AND")
    @patch("aol_email_exporter.client.MailBox")
    def test_fetch_with_sender_filter(self, mock_mailbox_cls, mock_and):
        mb = _mock_mailbox()
        mock_mailbox_cls.return_value = mb
        mock_and.return_value = MagicMock()

        client = AOLClient("user@aol.com", "pass")
        client.connect()

        filters = FilterParams(sender="alice@aol.com")
        client.fetch_emails(filters)

        mock_and.assert_called_once()
        call_kwargs = mock_and.call_args[1]
        assert call_kwargs["from_"] == "alice@aol.com"
