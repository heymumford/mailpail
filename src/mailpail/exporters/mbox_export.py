# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import email
import email.utils
import hashlib
import logging
import mailbox
from pathlib import Path

from mailpail.models import EmailRecord, ExportConfig, ExportResult

logger = logging.getLogger(__name__)


class MboxExporter:
    """Export emails to a standard MBOX file."""

    def export(self, records: list[EmailRecord], config: ExportConfig) -> ExportResult:
        out_dir = Path(config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{config.filename_prefix}.mbox"

        warnings: list[str] = []
        att_count = 0
        try:
            mbox = mailbox.mbox(str(out_path))
            mbox.lock()

            try:
                for rec in records:
                    msg = self._record_to_message(rec, config.include_attachments)
                    if config.include_attachments:
                        att_count += len(rec.attachments)
                    mbox.add(msg)
            finally:
                mbox.unlock()
                mbox.close()

            file_hash = hashlib.sha256(out_path.read_bytes()).hexdigest()
            logger.info("MBOX export complete: %d records -> %s", len(records), out_path)

            return ExportResult(
                format_name="mbox",
                file_path=str(out_path),
                record_count=len(records),
                success=True,
                warnings=warnings,
                attachment_count=att_count,
                sha256=file_hash,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("MBOX export failed: %s", exc)
            return ExportResult(
                format_name="mbox",
                file_path=str(out_path),
                record_count=0,
                success=False,
                error=str(exc),
                warnings=warnings,
            )

    @staticmethod
    def _record_to_message(rec: EmailRecord, include_attachments: bool) -> email.message.Message:
        if rec.attachments and include_attachments:
            msg = email.message.EmailMessage()
            msg.make_mixed()
            msg.attach(email.message.EmailMessage())
            body_part = msg.get_payload()[0]
            body_part.set_content(rec.body_text or "(no text content)")
            for att in rec.attachments:
                maintype, _, subtype = att.content_type.partition("/")
                msg.add_attachment(
                    att.payload,
                    maintype=maintype or "application",
                    subtype=subtype or "octet-stream",
                    filename=att.filename,
                )
        else:
            msg = email.message.EmailMessage()
            msg.set_content(rec.body_text or "(no text content)")

        msg["From"] = rec.sender
        msg["To"] = rec.to
        if rec.cc:
            msg["Cc"] = rec.cc
        msg["Subject"] = rec.subject
        msg["Message-ID"] = rec.message_id or f"<{rec.uid}@mailpail>"
        if rec.date:
            msg["Date"] = email.utils.format_datetime(rec.date)

        return msg
