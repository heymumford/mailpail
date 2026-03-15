# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime
import logging
from pathlib import Path

from fpdf import FPDF

from aol_email_exporter.models import EmailRecord, ExportConfig, ExportResult

logger = logging.getLogger(__name__)

_PAGE_WIDTH_MM = 190  # usable width (A4 minus margins)


class PdfExporter:
    """Export emails to a PDF document using fpdf2."""

    def export(self, records: list[EmailRecord], config: ExportConfig) -> ExportResult:
        out_dir = Path(config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{config.filename_prefix}.pdf"

        warnings: list[str] = []
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Title page
            self._write_title_page(pdf, records, config)

            # Individual emails
            for rec in records:
                self._write_email(pdf, rec, warnings)

            pdf.output(str(out_path))
            logger.info("PDF export complete: %d records -> %s", len(records), out_path)

            if warnings:
                logger.warning("PDF export produced %d warnings", len(warnings))

            return ExportResult(
                format_name="pdf",
                file_path=str(out_path),
                record_count=len(records),
                success=True,
                warnings=warnings,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("PDF export failed: %s", exc)
            return ExportResult(
                format_name="pdf",
                file_path=str(out_path),
                record_count=0,
                success=False,
                error=str(exc),
                warnings=warnings,
            )

    # -- Internal ---------------------------------------------------------

    @staticmethod
    def _write_title_page(pdf: FPDF, records: list[EmailRecord], config: ExportConfig) -> None:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 20, config.pdf_title, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)

        pdf.set_font("Helvetica", "", 12)
        generated = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
        pdf.cell(0, 8, f"Generated: {generated}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Total emails: {len(records)}", new_x="LMARGIN", new_y="NEXT")

        if records:
            dates = [r.date for r in records if r.date]
            if dates:
                earliest = min(dates).strftime("%Y-%m-%d")
                latest = max(dates).strftime("%Y-%m-%d")
                pdf.cell(0, 8, f"Date range: {earliest} to {latest}", new_x="LMARGIN", new_y="NEXT")

            folders = sorted({r.folder for r in records if r.folder})
            if folders:
                pdf.cell(0, 8, f"Folders: {', '.join(folders)}", new_x="LMARGIN", new_y="NEXT")

    @staticmethod
    def _write_email(pdf: FPDF, rec: EmailRecord, warnings: list[str]) -> None:
        pdf.add_page()

        # Subject (bold)
        pdf.set_font("Helvetica", "B", 14)
        subject = rec.subject or "(no subject)"
        pdf.multi_cell(0, 8, subject, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Metadata
        pdf.set_font("Helvetica", "", 10)
        date_str = rec.date.strftime("%Y-%m-%d %H:%M:%S") if rec.date else "Unknown"
        pdf.cell(0, 6, f"Date: {date_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"From: {rec.sender}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"To: {rec.to}", new_x="LMARGIN", new_y="NEXT")
        if rec.cc:
            pdf.cell(0, 6, f"CC: {rec.cc}", new_x="LMARGIN", new_y="NEXT")
        if rec.has_attachments:
            pdf.cell(0, 6, "Attachments: Yes", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # Body
        pdf.set_font("Helvetica", "", 10)
        body = rec.body_text or "(no text content)"
        # Helvetica covers basic Latin only; replace characters that will fail.
        try:
            pdf.multi_cell(0, 5, body)
        except Exception:  # noqa: BLE001
            safe_body = body.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 5, safe_body)
            warnings.append(
                f"Unicode characters in email '{rec.subject}' (message-id {rec.message_id}) "
                "were replaced — Helvetica font has limited character coverage"
            )
