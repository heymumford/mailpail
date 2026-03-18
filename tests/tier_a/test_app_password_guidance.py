# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier A — App password setup guidance is visible and correct.

These are MUST-PASS tests. Without app password guidance, no AOL user
can complete the login flow. This is the #1 reason users report
"adding email accounts doesn't work."
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.tier_a


class TestAppPasswordSetupStrings:
    """Every provider has setup instructions in strings.py."""

    def test_aol_setup_instructions_exist(self):
        from mailpail.ui.strings import APP_PASSWORD_SETUP

        assert "aol" in APP_PASSWORD_SETUP
        text = APP_PASSWORD_SETUP["aol"]
        assert "app password" in text.lower()
        assert "2-step" in text.lower() or "2-factor" in text.lower() or "verification" in text.lower()

    def test_gmail_setup_instructions_exist(self):
        from mailpail.ui.strings import APP_PASSWORD_SETUP

        assert "gmail" in APP_PASSWORD_SETUP
        assert "app password" in APP_PASSWORD_SETUP["gmail"].lower()

    def test_outlook_setup_instructions_exist(self):
        from mailpail.ui.strings import APP_PASSWORD_SETUP

        assert "outlook" in APP_PASSWORD_SETUP
        assert "app password" in APP_PASSWORD_SETUP["outlook"].lower()

    def test_yahoo_setup_instructions_exist(self):
        from mailpail.ui.strings import APP_PASSWORD_SETUP

        assert "yahoo" in APP_PASSWORD_SETUP
        assert "app password" in APP_PASSWORD_SETUP["yahoo"].lower()

    def test_every_provider_has_setup_instructions(self):
        """Every registered provider key has a matching setup instruction."""
        from mailpail.providers import PROVIDERS
        from mailpail.ui.strings import APP_PASSWORD_SETUP

        for key in PROVIDERS:
            assert key in APP_PASSWORD_SETUP, f"Provider '{key}' missing from APP_PASSWORD_SETUP"

    def test_setup_instructions_mention_regular_password_wont_work(self):
        """AOL setup instructions explicitly say regular password won't work."""
        from mailpail.ui.strings import APP_PASSWORD_SETUP

        aol_text = APP_PASSWORD_SETUP["aol"].lower()
        assert "regular password" in aol_text or "won't work" in aol_text

    def test_setup_instructions_are_step_by_step(self):
        """AOL instructions have numbered steps."""
        from mailpail.ui.strings import APP_PASSWORD_SETUP

        aol_text = APP_PASSWORD_SETUP["aol"]
        assert "1." in aol_text
        assert "2." in aol_text
        assert "3." in aol_text


class TestAppPasswordHelpURLs:
    """Every provider has a help URL that points to app password setup."""

    def test_aol_help_url(self):
        from mailpail.providers import PROVIDERS

        assert "aol.com" in PROVIDERS["aol"].help_url
        assert "security" in PROVIDERS["aol"].help_url or "password" in PROVIDERS["aol"].help_url

    def test_gmail_help_url(self):
        from mailpail.providers import PROVIDERS

        assert "google" in PROVIDERS["gmail"].help_url

    def test_outlook_help_url(self):
        from mailpail.providers import PROVIDERS

        assert "microsoft" in PROVIDERS["outlook"].help_url

    def test_yahoo_help_url(self):
        from mailpail.providers import PROVIDERS

        assert "yahoo" in PROVIDERS["yahoo"].help_url

    def test_all_providers_except_custom_have_help_url(self):
        from mailpail.providers import PROVIDERS

        for key, desc in PROVIDERS.items():
            if key == "imap":
                continue  # custom IMAP has no help URL
            assert desc.help_url, f"Provider '{key}' has no help_url"


class TestAuthFailureMessages:
    """Auth failure produces a helpful message, not a stack trace."""

    def test_auth_failed_message_mentions_app_password(self):
        from mailpail.ui.strings import LOGIN_AUTH_FAILED

        text = LOGIN_AUTH_FAILED.lower()
        assert "app password" in text
        assert "regular password" in text

    def test_network_failed_message_mentions_connection(self):
        from mailpail.ui.strings import LOGIN_NETWORK_FAILED

        text = LOGIN_NETWORK_FAILED.lower()
        assert "internet" in text or "connection" in text

    def test_client_auth_error_is_categorized(self):
        """IMAPClient raises ConnectionError with 'authentication' for wrong creds."""
        from unittest.mock import MagicMock, patch

        from mailpail.client import IMAPClient

        with patch("mailpail.client.MailBox") as mock_cls:
            mb = MagicMock()
            mb.login.side_effect = Exception("AUTHENTICATIONFAILED Invalid credentials")
            mock_cls.return_value = mb

            client = IMAPClient("u@aol.com", "wrong")
            with pytest.raises(ConnectionError) as exc_info:
                client.connect()

            msg = str(exc_info.value).lower()
            assert "authentication" in msg or "app password" in msg

    def test_client_network_error_is_categorized(self):
        """IMAPClient raises ConnectionError with network hint for connection issues."""
        from unittest.mock import patch

        from mailpail.client import IMAPClient

        with patch("mailpail.client.MailBox") as mock_cls:
            mock_cls.side_effect = Exception("Connection refused")

            client = IMAPClient("u@aol.com", "pass")
            with pytest.raises(ConnectionError) as exc_info:
                client.connect()

            msg = str(exc_info.value).lower()
            assert "reach" in msg or "refused" in msg or "connection" in msg


class TestPasswordFieldLabel:
    """The password field says 'App Password', not 'Password'."""

    def test_password_label_says_app_password(self):
        from mailpail.ui.strings import LOGIN_PASSWORD_LABEL

        assert "app" in LOGIN_PASSWORD_LABEL.lower()
        assert "password" in LOGIN_PASSWORD_LABEL.lower()

    def test_password_placeholder_says_app_password(self):
        from mailpail.ui.strings import LOGIN_PASSWORD_PLACEHOLDER

        assert "app" in LOGIN_PASSWORD_PLACEHOLDER.lower()

    def test_help_link_mentions_app_password(self):
        from mailpail.ui.strings import LOGIN_HELP_LINK

        assert "app password" in LOGIN_HELP_LINK.lower()
