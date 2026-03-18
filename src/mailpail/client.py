# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from types import TracebackType

from imap_tools import AND, MailBox, MailBoxUnencrypted, MailMessage

from mailpail.models import Attachment, EmailRecord, FilterParams

logger = logging.getLogger(__name__)


class IMAPClient:
    """IMAP client wrapper using imap_tools.

    Satisfies the ``EmailProvider`` Protocol defined in ``providers.py``.
    """

    def __init__(
        self,
        username: str,
        password: str,
        server: str = "export.imap.aol.com",
        port: int = 993,
        *,
        use_ssl: bool = True,
    ) -> None:
        self._username = username
        self._password = password
        self._server = server
        self._port = port
        self._use_ssl = use_ssl
        self._mailbox: MailBox | MailBoxUnencrypted | None = None

    @property
    def display_name(self) -> str:
        return f"IMAP ({self._server})"

    # -- Context manager --------------------------------------------------

    def __enter__(self) -> IMAPClient:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.disconnect()

    # -- Connection -------------------------------------------------------

    def connect(self) -> None:
        """Establish a connection and authenticate.

        For AOL: tries the configured server first. If auth fails on
        export.imap.aol.com, retries on imap.aol.com (regular passwords
        may only work on the standard server).
        """
        exc = self._try_connect(self._server, self._port)
        if exc is None:
            return

        # AOL fallback: export server may reject regular passwords
        if self._server == "export.imap.aol.com":
            logger.info("Retrying on imap.aol.com (regular password may work there)")
            fallback_exc = self._try_connect("imap.aol.com", 993)
            if fallback_exc is None:
                self._server = "imap.aol.com"
                return

        self._raise_connection_error(exc)

    def _try_connect(self, server: str, port: int) -> Exception | None:
        """Attempt connection. Returns None on success, exception on failure."""
        logger.info("Connecting to %s:%d as %s (ssl=%s)", server, port, self._username, self._use_ssl)
        try:
            if self._use_ssl:
                self._mailbox = MailBox(server, port)
            else:
                self._mailbox = MailBoxUnencrypted(server, port)
            self._mailbox.login(self._username, self._password)
            logger.info("Connected successfully to %s:%d", server, port)
            return None
        except Exception as exc:
            self._mailbox = None
            return exc

    def _raise_connection_error(self, exc: Exception) -> None:
        """Raise a ConnectionError with a user-friendly message."""
        error_str = str(exc).lower()
        if "authentication" in error_str or "login" in error_str or "credentials" in error_str:
            msg = (
                f"Authentication failed for {self._username} — "
                "check your password. If your regular password didn't work, "
                "you may need an app password from your email provider."
            )
        elif "ssl" in error_str or "tls" in error_str or "handshake" in error_str:
            msg = (
                f"SSL/TLS connection failed to {self._server}:{self._port} — "
                "verify the server address and port are correct."
            )
        elif "refused" in error_str or "timeout" in error_str or "resolve" in error_str:
            msg = (
                f"Could not reach {self._server}:{self._port} — "
                "check your internet connection and verify the server address."
            )
        else:
            msg = f"Failed to connect to {self._server}:{self._port} — check your email and password. Detail: {exc}"
        logger.error(msg)
        raise ConnectionError(msg) from exc

    def disconnect(self) -> None:
        """Log out and close the connection."""
        if self._mailbox is not None:
            try:
                self._mailbox.logout()
                logger.info("Disconnected from %s", self._server)
            except Exception:  # noqa: BLE001
                logger.debug("Logout raised an exception (ignored)")
            finally:
                self._mailbox = None

    # -- Queries ----------------------------------------------------------

    def _ensure_connected(self) -> MailBox:
        if self._mailbox is None:
            raise ConnectionError("Not connected — call connect() first")
        return self._mailbox

    def list_folders(self) -> list[str]:
        """Return the names of all IMAP folders in the account."""
        mailbox = self._ensure_connected()
        folders = [f.name for f in mailbox.folder.list()]
        logger.info("Found %d folders", len(folders))
        return folders

    def fetch_emails(self, filters: FilterParams) -> list[EmailRecord]:
        """Fetch emails matching *filters* and return as EmailRecord list.

        Server-side IMAP criteria are built from FilterParams where possible.
        """
        mailbox = self._ensure_connected()
        folder = filters.folder or "INBOX"

        mailbox.folder.set(folder)
        logger.info("Fetching from folder: %s", folder)

        criteria = self._build_criteria(filters)
        records: list[EmailRecord] = []

        for idx, msg in enumerate(mailbox.fetch(criteria, mark_seen=False), start=1):
            records.append(self._msg_to_record(msg, folder))
            if idx % 100 == 0:
                logger.info("Fetched %d messages so far...", idx)

        logger.info("Fetch complete: %d messages from %s", len(records), folder)
        return records

    # -- Internal ---------------------------------------------------------

    @staticmethod
    def _build_criteria(filters: FilterParams) -> AND:
        """Translate FilterParams into an imap_tools AND criterion."""
        parts: dict[str, object] = {}

        if filters.date_from is not None:
            parts["date_gte"] = filters.date_from
        if filters.date_to is not None:
            parts["date_lt"] = filters.date_to
        if filters.sender:
            parts["from_"] = filters.sender
        if filters.subject:
            parts["subject"] = filters.subject
        if filters.unread_only:
            parts["seen"] = False

        return AND(**parts) if parts else "ALL"

    @staticmethod
    def _msg_to_record(msg: MailMessage, folder: str) -> EmailRecord:
        atts = tuple(
            Attachment(
                filename=a.filename or "unnamed",
                content_type=a.content_type or "application/octet-stream",
                payload=a.payload,
                size=len(a.payload),
            )
            for a in msg.attachments
        )
        return EmailRecord(
            uid=msg.uid or "",
            date=msg.date,
            sender=msg.from_ or "",
            to=", ".join(msg.to),
            cc=", ".join(msg.cc),
            subject=msg.subject or "",
            body_text=msg.text or "",
            body_html=msg.html or "",
            folder=folder,
            has_attachments=bool(msg.attachments),
            message_id=msg.headers.get("message-id", ("",))[0] if msg.headers.get("message-id") else "",
            size_bytes=len(msg.obj.as_bytes()) if msg.obj else 0,
            attachments=atts,
        )
