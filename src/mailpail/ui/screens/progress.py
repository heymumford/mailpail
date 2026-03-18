# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import customtkinter

from mailpail.exporters import get_exporter
from mailpail.filters import apply_filters
from mailpail.models import ExportConfig, ExportResult, FilterParams
from mailpail.ui.strings import PROGRESS_REASSURANCE
from mailpail.ui.theme import COLORS, FONTS, ICONS

if TYPE_CHECKING:
    from mailpail.client import IMAPClient
    from mailpail.ui.app import MailpailApp

logger = logging.getLogger(__name__)


class _UILogHandler(logging.Handler):
    """Logging handler that forwards records to the progress screen."""

    def __init__(self, callback: object) -> None:
        super().__init__()
        self._callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        try:
            self._callback(msg)  # type: ignore[operator]
        except Exception:
            pass


class ProgressScreen(customtkinter.CTkFrame):
    """Wizard step 6 — download and export progress with live feedback."""

    def __init__(self, parent: customtkinter.CTkFrame, app: MailpailApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._cancel_event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._log_handler: _UILogHandler | None = None
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=2)

        # Header
        header_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        header_frame.grid(row=1, column=0, pady=(0, 8))

        customtkinter.CTkLabel(
            header_frame,
            text=ICONS["progress"],
            font=FONTS["icon"],
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 12))

        self._header_label = customtkinter.CTkLabel(
            header_frame,
            text="Downloading Emails",
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["fg"],
        )
        self._header_label.pack(side="left")

        # Current folder label
        self._folder_label = customtkinter.CTkLabel(
            self,
            text="Preparing...",
            font=FONTS["body"],
            text_color=COLORS["subtle"],
        )
        self._folder_label.grid(row=2, column=0, pady=(0, 12))

        # Progress bar
        self._progress_bar = customtkinter.CTkProgressBar(
            self,
            width=500,
            height=20,
            corner_radius=10,
            progress_color=COLORS["accent"],
        )
        self._progress_bar.grid(row=3, column=0, padx=80, pady=(0, 8), sticky="ew")
        self._progress_bar.set(0)

        # Count label
        self._count_label = customtkinter.CTkLabel(
            self,
            text="",
            font=FONTS["body"],
            text_color=COLORS["fg"],
        )
        self._count_label.grid(row=4, column=0, pady=(0, 16))

        # Log preview
        self._log_text = customtkinter.CTkTextbox(
            self,
            font=FONTS["small"],
            height=100,
            corner_radius=8,
            fg_color=COLORS["card"],
            text_color=COLORS["subtle"],
            border_width=1,
            border_color=COLORS["border"],
            state="disabled",
        )
        self._log_text.grid(row=5, column=0, padx=80, pady=(0, 12), sticky="ew")

        # Reassurance text
        customtkinter.CTkLabel(
            self,
            text=PROGRESS_REASSURANCE,
            font=FONTS["label"],
            text_color=COLORS["success"],
        ).grid(row=6, column=0, pady=(0, 12))

        # Cancel button
        self._cancel_btn = customtkinter.CTkButton(
            self,
            text="Cancel",
            font=FONTS["label"],
            fg_color=COLORS["error"],
            hover_color=COLORS["error_hover"],
            text_color=COLORS["button_text"],
            corner_radius=8,
            height=40,
            width=140,
            command=self._cancel_download,
        )
        self._cancel_btn.grid(row=7, column=0, pady=(0, 8))

    def on_show(self) -> None:
        """Called when this screen becomes visible. Start the download."""
        self._cancel_event.clear()
        self._start_download()

    def _append_log(self, message: str) -> None:
        """Append a message to the log preview (thread-safe)."""

        def _do() -> None:
            self._log_text.configure(state="normal")
            self._log_text.insert("end", message + "\n")
            lines = self._log_text.get("1.0", "end").strip().split("\n")
            if len(lines) > 5:
                self._log_text.delete("1.0", "end")
                self._log_text.insert("1.0", "\n".join(lines[-5:]) + "\n")
            self._log_text.see("end")
            self._log_text.configure(state="disabled")

        self._app.run_on_main(_do)

    def _start_download(self) -> None:
        """Launch the download/export worker thread."""
        # Install log handler
        self._log_handler = _UILogHandler(self._append_log)
        self._log_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger("mailpail").addHandler(self._log_handler)

        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _ui(self, func: Any, *args: Any) -> None:
        """Thread-safe UI update — posts to the app's main-thread queue."""
        self._app.run_on_main(func, *args)

    def _worker(self) -> None:
        """Background worker: fetch emails from each folder, apply filters, export."""
        state = self._app.wizard_state
        client: IMAPClient = state["client"]
        folders: list[str] = state.get("selected_folders", ["INBOX"])
        filters: FilterParams = state.get("filters", FilterParams())
        formats: list[str] = state.get("formats", ["csv"])
        output_dir: str = state.get("output_dir", os.path.join(os.path.expanduser("~"), "Desktop", "Mailpail_Export"))

        os.makedirs(output_dir, exist_ok=True)

        all_records = []
        total_folders = len(folders)
        results: list[ExportResult] = []

        try:
            for folder_idx, folder_name in enumerate(folders):
                if self._cancel_event.is_set():
                    self._ui(self._on_cancelled)
                    return

                self._ui(
                    self._update_status,
                    f"Downloading from: {folder_name}",
                    f"Folder {folder_idx + 1} of {total_folders}",
                )

                folder_filters = FilterParams(
                    date_from=filters.date_from,
                    date_to=filters.date_to,
                    sender=filters.sender,
                    subject=filters.subject,
                    folder=folder_name,
                    unread_only=filters.unread_only,
                )

                records = client.fetch_emails(folder_filters)
                records = apply_filters(records, folder_filters)
                all_records.extend(records)

                progress = (folder_idx + 1) / total_folders * 0.7
                self._ui(self._set_progress, progress)
                self._ui(self._update_count, f"Downloaded {len(all_records):,} emails so far")

            if self._cancel_event.is_set():
                self._ui(self._on_cancelled)
                return

            self._ui(self._update_status, "Exporting...", f"{len(all_records):,} emails total")

            export_config = ExportConfig(output_dir=output_dir, formats=tuple(formats))

            for fmt_idx, fmt_name in enumerate(formats):
                if self._cancel_event.is_set():
                    self._ui(self._on_cancelled)
                    return

                self._ui(self._update_status, f"Exporting as {fmt_name}...", "")

                exporter = get_exporter(fmt_name)
                result = exporter.export(all_records, export_config)
                results.append(result)

                progress = 0.7 + ((fmt_idx + 1) / len(formats)) * 0.3
                self._ui(self._set_progress, progress)

            # Write export log
            from mailpail.exporters.export_log import write_export_log

            write_export_log(
                Path(output_dir),
                results,
                len(all_records),
                filters=filters,
                folders=folders,
                provider_key=state.get("provider_key", ""),
                username=state.get("username", ""),
            )
            self._ui(self._append_log, "Export log written")

            # Save incremental UIDs only if all exports succeeded
            if all(r.success for r in results):
                from mailpail.exporters.incremental import save_exported_uids

                exported_uids = {r.uid for r in all_records}
                save_exported_uids(Path(output_dir), exported_uids)

            # Write manifest
            from mailpail.exporters.manifest import write_manifest

            manifest_path = write_manifest(Path(output_dir), results, len(all_records))
            self._ui(self._append_log, f"Manifest: {manifest_path.name}")

            # Zip the entire export
            from mailpail.exporters.zipper import zip_export

            self._ui(self._update_status, "Creating zip archive...", "")
            zip_path = zip_export(Path(output_dir))
            state["zip_path"] = str(zip_path)
            self._ui(self._append_log, f"Zip: {zip_path.name}")

            state["results"] = results
            state["total_emails"] = len(all_records)
            self._ui(self._set_progress, 1.0)
            self._ui(self._update_status, "Export complete!", "")
            # Delay advance to Complete screen
            self._app.run_on_main(lambda: self.after(1000, self._on_complete))

        except Exception as exc:
            logger.exception("Export failed")
            self._ui(self._on_error, str(exc))
        finally:
            if self._log_handler is not None:
                logging.getLogger("mailpail").removeHandler(self._log_handler)
                self._log_handler = None

    def _update_status(self, folder_text: str, count_text: str) -> None:
        self._folder_label.configure(text=folder_text)
        if count_text:
            self._count_label.configure(text=count_text)

    def _update_count(self, text: str) -> None:
        self._count_label.configure(text=text)

    def _set_progress(self, value: float) -> None:
        self._progress_bar.set(value)

    def _cancel_download(self) -> None:
        self._cancel_event.set()
        self._cancel_btn.configure(state="disabled", text="Cancelling...")

    def _on_cancelled(self) -> None:
        self._folder_label.configure(text="Download cancelled.", text_color=COLORS["warning"])
        self._cancel_btn.configure(state="normal", text="Cancel")
        self._app.enable_back()

    def _on_error(self, error_msg: str) -> None:
        display = error_msg if len(error_msg) < 300 else error_msg[:300] + "..."
        self._folder_label.configure(
            text=f"{ICONS['error']} Error: {display}",
            text_color=COLORS["error"],
        )
        self._cancel_btn.configure(state="normal", text="Cancel")
        self._app.enable_back()

    def _on_complete(self) -> None:
        """Auto-advance to the complete screen."""
        self._app.go_next()
