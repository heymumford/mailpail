# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier A — Live IMAP tests against real email servers.

These tests connect to real IMAP servers using credentials from .env.
They are SKIPPED when credentials are not set.

To run:
    1. Fill in .env with real credentials
    2. just test-live

Environment variables:
    MAILPAIL_AOL_USERNAME — AOL email address
    MAILPAIL_AOL_PASSWORD — AOL app password
"""

from __future__ import annotations

import os

import pytest

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

_AOL_USER = os.environ.get("MAILPAIL_AOL_USERNAME", "")
_AOL_PASS = os.environ.get("MAILPAIL_AOL_PASSWORD", "")
_HAS_AOL_CREDS = bool(_AOL_USER and _AOL_PASS and _AOL_USER != "your.email@aol.com")

pytestmark = [
    pytest.mark.tier_a,
    pytest.mark.live,
    pytest.mark.skipif(not _HAS_AOL_CREDS, reason="No AOL credentials in .env"),
]


class TestLiveAOLConnection:
    """Connect to the real AOL IMAP server."""

    def test_connect_and_disconnect(self):
        from mailpail.client import IMAPClient

        client = IMAPClient(
            username=_AOL_USER,
            password=_AOL_PASS,
            server="export.imap.aol.com",
            port=993,
        )
        client.connect()
        client.disconnect()

    def test_list_folders(self):
        from mailpail.client import IMAPClient

        with IMAPClient(
            username=_AOL_USER,
            password=_AOL_PASS,
            server="export.imap.aol.com",
            port=993,
        ) as client:
            folders = client.list_folders()

        assert len(folders) > 0
        assert "INBOX" in folders
        # AOL-specific folder names
        print(f"  AOL folders: {folders}")

    def test_fetch_inbox_limited(self):
        """Fetch first few emails from real INBOX."""
        from mailpail.client import IMAPClient
        from mailpail.models import FilterParams

        with IMAPClient(
            username=_AOL_USER,
            password=_AOL_PASS,
            server="export.imap.aol.com",
            port=993,
        ) as client:
            records = client.fetch_emails(FilterParams(folder="INBOX"))

        # Just verify we got something and it has structure
        assert len(records) > 0
        first = records[0]
        assert first.uid
        assert first.sender
        assert first.subject is not None
        print(f"  Fetched {len(records)} emails from AOL INBOX")
        print(f"  First: uid={first.uid}, from={first.sender}, subject={first.subject[:50]}")

    def test_full_csv_export(self, tmp_path):
        """Full pipeline: connect → fetch → filter → export → verify."""
        from mailpail.client import IMAPClient
        from mailpail.exporters import get_exporter
        from mailpail.exporters.manifest import write_manifest
        from mailpail.exporters.zipper import zip_export
        from mailpail.filters import apply_filters
        from mailpail.models import ExportConfig, FilterParams

        with IMAPClient(
            username=_AOL_USER,
            password=_AOL_PASS,
            server="export.imap.aol.com",
            port=993,
        ) as client:
            records = client.fetch_emails(FilterParams(folder="INBOX"))

        records = apply_filters(records, FilterParams())

        config = ExportConfig(
            output_dir=str(tmp_path),
            filename_prefix="live_aol_test",
        )
        result = get_exporter("csv").export(records, config)
        assert result.success
        assert result.record_count > 0

        manifest_path = write_manifest(tmp_path, [result], total_emails=len(records))
        assert manifest_path.exists()

        zip_path = zip_export(tmp_path)
        assert zip_path.exists()

        print(f"  Exported {result.record_count} emails to {tmp_path}")
        print(f"  Attachments: {result.attachment_count}")
        print(f"  Zip: {zip_path.name} ({zip_path.stat().st_size} bytes)")
