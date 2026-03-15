# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from types import TracebackType

from imap_tools import AND, MailBox, MailMessage

from mailpail.models import EmailRecord, FilterParams

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
    ) -> None:
        self._username = username
        self._password = password
        self._server = server
        self._port = port
        self._mailbox: MailBox | None = None

    @property
    def display_name(self) -> str:
        return "AOL Mail"

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
        """Establish an SSL connection and authenticate."""
        logger.info("Connecting to %s:%d as %s", self._server, self._port, self._username)
        try:
            self._mailbox = MailBox(self._server, self._port)
            self._mailbox.login(self._username, self._password)
            logger.info("Connected successfully")
        except Exception as exc:
            msg = (
                f"Failed to connect to {self._server}:{self._port} — "
                "verify your app password (not your regular password). "
                "Check your email provider's app password settings."
            )
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
        )
