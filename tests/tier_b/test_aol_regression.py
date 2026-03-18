# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier B — AOL-specific regression and edge case tests.

Covers AOL folder naming quirks, error handling, auth edge cases,
large mailbox behavior, and provider configuration.
"""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from mailpail.auth import AppPasswordFlow, AuthError, Credential
from mailpail.client import IMAPClient
from mailpail.filters import apply_filters
from mailpail.models import FilterParams
from mailpail.providers import PROVIDERS

pytestmark = pytest.mark.tier_b


class TestAOLProviderConfig:
    """AOL provider is correctly configured for the export use case."""

    def test_aol_uses_export_server(self):
        """AOL provider uses export.imap.aol.com (not imap.aol.com)."""
        assert PROVIDERS["aol"].server == "export.imap.aol.com"

    def test_aol_uses_port_993(self):
        assert PROVIDERS["aol"].port == 993

    def test_aol_has_help_url(self):
        assert "aol.com" in PROVIDERS["aol"].help_url

    def test_aol_name_is_aol_mail(self):
        assert PROVIDERS["aol"].name == "AOL Mail"

    def test_aol_adapter_factory_creates_client(self):
        cred = Credential(provider_key="aol", data={"username": "u@aol.com", "password": "p"})
        client = PROVIDERS["aol"].adapter_factory(cred)
        assert isinstance(client, IMAPClient)
        assert client._server == "export.imap.aol.com"

    def test_aol_auth_flow_is_app_password(self):
        flow = PROVIDERS["aol"].auth_flow
        assert isinstance(flow, AppPasswordFlow)
        assert flow.requires_browser is False

    def test_aol_form_fields(self):
        """AOL login form has email and password fields."""
        fields = PROVIDERS["aol"].auth_flow.form_fields()
        assert len(fields) == 2
        assert fields[0].key == "username"
        assert fields[0].label == "Email Address"
        assert fields[1].key == "password"
        assert fields[1].secret is True


class TestAOLFolderQuirks:
    """AOL uses non-standard folder names. Verify our code handles them."""

    @patch("mailpail.client.MailBox")
    def test_draft_singular(self, mock_mb_cls):
        """AOL uses 'Draft' (singular), not 'Drafts'."""
        mb = MagicMock()
        f = MagicMock()
        f.name = "Draft"
        mb.folder.list.return_value = [f]
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "p")
        client.connect()
        folders = client.list_folders()
        assert "Draft" in folders

    @patch("mailpail.client.MailBox")
    def test_bulk_mail_spam_folder(self, mock_mb_cls):
        """AOL's spam folder is 'Bulk Mail', not 'Spam' or 'Junk'."""
        mb = MagicMock()
        f = MagicMock()
        f.name = "Bulk Mail"
        mb.folder.list.return_value = [f]
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "p")
        client.connect()
        folders = client.list_folders()
        assert "Bulk Mail" in folders

    @patch("mailpail.client.MailBox")
    def test_fetch_from_bulk_mail_folder(self, mock_mb_cls):
        """Can fetch from 'Bulk Mail' folder (spaces in name)."""
        mb = MagicMock()
        mb.fetch.return_value = iter([])
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "p")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="Bulk Mail"))

        mb.folder.set.assert_called_once_with("Bulk Mail")
        assert records == []


class TestAOLErrorHandling:
    """Common AOL connection errors produce clear messages."""

    @patch("mailpail.client.MailBox")
    def test_wrong_password_error(self, mock_mb_cls):
        """Wrong password produces helpful error mentioning app password."""
        mb = MagicMock()
        mb.login.side_effect = Exception("AUTHENTICATIONFAILED")
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "wrong-password")
        with pytest.raises(ConnectionError, match="app password"):
            client.connect()

    @patch("mailpail.client.MailBox")
    def test_connection_refused_error(self, mock_mb_cls):
        """Connection refused produces helpful error."""
        mock_mb_cls.side_effect = Exception("Connection refused")

        client = IMAPClient("u@aol.com", "pass")
        with pytest.raises(ConnectionError):
            client.connect()

    @patch("mailpail.client.MailBox")
    def test_rate_limit_error(self, mock_mb_cls):
        """Rate limit error is caught."""
        mb = MagicMock()
        mb.login.side_effect = Exception("AUTHENTICATE Rate limit hit")
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "pass")
        with pytest.raises(ConnectionError):
            client.connect()

    def test_app_password_empty_rejects(self):
        """Empty credentials raise AuthError, not a cryptic IMAP error."""
        flow = AppPasswordFlow(provider_key="aol")
        with pytest.raises(AuthError, match="required"):
            flow.acquire({"username": "u@aol.com", "password": ""})

    def test_app_password_whitespace_rejects(self):
        """Whitespace-only credentials raise AuthError."""
        flow = AppPasswordFlow(provider_key="aol")
        with pytest.raises(AuthError, match="required"):
            flow.acquire({"username": "  ", "password": "  "})


class TestAOLEdgeCases:
    """Edge cases specific to AOL mail patterns."""

    @patch("mailpail.client.MailBox")
    def test_empty_inbox(self, mock_mb_cls):
        """Handle empty inbox gracefully."""
        mb = MagicMock()
        mb.fetch.return_value = iter([])
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "p")
        client.connect()
        records = client.fetch_emails(FilterParams(folder="INBOX"))
        assert records == []

    @patch("mailpail.client.MailBox")
    def test_no_folders(self, mock_mb_cls):
        """Handle account with no folders."""
        mb = MagicMock()
        mb.folder.list.return_value = []
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "p")
        client.connect()
        folders = client.list_folders()
        assert folders == []

    def test_filter_case_insensitive_sender(self):
        """Sender filter is case-insensitive."""
        from mailpail.models import EmailRecord

        rec = EmailRecord(
            uid="1",
            date=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            sender="Alice@AOL.COM",
            to="me@aol.com",
            cc="",
            subject="Test",
            body_text="Body",
            body_html="",
            folder="INBOX",
            has_attachments=False,
            message_id="<1@aol>",
        )
        result = apply_filters([rec], FilterParams(sender="alice@aol.com"))
        assert len(result) == 1

    def test_filter_case_insensitive_subject(self):
        """Subject filter is case-insensitive."""
        from mailpail.models import EmailRecord

        rec = EmailRecord(
            uid="1",
            date=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            sender="x@aol.com",
            to="me@aol.com",
            cc="",
            subject="IMPORTANT: Tax Documents",
            body_text="Body",
            body_html="",
            folder="INBOX",
            has_attachments=False,
            message_id="<1@aol>",
        )
        result = apply_filters([rec], FilterParams(subject="tax documents"))
        assert len(result) == 1

    @patch("mailpail.client.MailBox")
    def test_disconnect_after_error(self, mock_mb_cls):
        """Disconnect doesn't crash even if connection failed."""
        mb = MagicMock()
        mb.logout.side_effect = Exception("Already disconnected")
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "p")
        client.connect()
        # Should not raise
        client.disconnect()

    @patch("mailpail.client.MailBox")
    def test_context_manager_cleanup(self, mock_mb_cls):
        """Context manager calls disconnect even on exception."""
        mb = MagicMock()
        mb.fetch.side_effect = Exception("Network error")
        mock_mb_cls.return_value = mb

        client = IMAPClient("u@aol.com", "p")
        try:
            with client:
                client.fetch_emails(FilterParams())
        except Exception:
            pass

        mb.logout.assert_called_once()
