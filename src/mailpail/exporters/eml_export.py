# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import email
import email.utils
import hashlib
import logging
import re
from pathlib import Path

from mailpail.models import EmailRecord, ExportConfig, ExportResult

logger = logging.getLogger(__name__)

_SAFE_CHARS = re.compile(r"[^\w\s\-.]")
_MAX_FILENAME_LEN = 80


def _safe_filename(subject: str, uid: str) -> str:
    """Create a filesystem-safe filename from subject + uid."""
    clean = _SAFE_CHARS.sub("_", subject or "no_subject").strip()[:_MAX_FILENAME_LEN]
    return f"{clean}_{uid}.eml"


class EmlExporter:
    """Export each email as an individual .eml file in a directory."""

    def export(self, records: list[EmailRecord], config: ExportConfig) -> ExportResult:
        out_dir = Path(config.output_dir) / f"{config.filename_prefix}_eml"
        out_dir.mkdir(parents=True, exist_ok=True)

        warnings: list[str] = []
        att_count = 0
        hasher = hashlib.sha256()
        try:
            for rec in records:
                msg = self._record_to_message(rec, config.include_attachments)
                if config.include_attachments:
                    att_count += len(rec.attachments)

                filename = _safe_filename(rec.subject, rec.uid)
                eml_path = out_dir / filename
                content = msg.as_bytes()
                eml_path.write_bytes(content)
                hasher.update(content)

            logger.info("EML export complete: %d records -> %s", len(records), out_dir)

            return ExportResult(
                format_name="eml",
                file_path=str(out_dir),
                record_count=len(records),
                success=True,
                warnings=warnings,
                attachment_count=att_count,
                sha256=hasher.hexdigest(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("EML export failed: %s", exc)
            return ExportResult(
                format_name="eml",
                file_path=str(out_dir),
                record_count=0,
                success=False,
                error=str(exc),
                warnings=warnings,
            )

    @staticmethod
    def _record_to_message(rec: EmailRecord, include_attachments: bool) -> email.message.EmailMessage:
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
