# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import platform
import subprocess
from typing import TYPE_CHECKING

import customtkinter

from mailpail.ui.theme import COLORS, FONTS, ICONS

if TYPE_CHECKING:
    from mailpail.models import ExportResult
    from mailpail.ui.app import MailpailApp

_CELEBRATION_COLORS = ["#007AFF", "#34C759", "#FF9500", "#FF3B30", "#AF52DE", "#5AC8FA"]


class CompleteScreen(customtkinter.CTkFrame):
    """Wizard step 7 — export summary, file locations, and celebratory finish."""

    def __init__(self, parent: customtkinter.CTkFrame, app: MailpailApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=2)

        # Checkmark icon
        self._icon = customtkinter.CTkLabel(
            self,
            text=ICONS["complete"],
            font=FONTS["icon_large"],
            text_color=COLORS["success"],
        )
        self._icon.grid(row=1, column=0, pady=(0, 8))

        # Header
        self._header = customtkinter.CTkLabel(
            self,
            text="Export Complete!",
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["success"],
        )
        self._header.grid(row=2, column=0, pady=(0, 16))

        # Summary card
        self._summary_card = customtkinter.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        self._summary_card.grid(row=3, column=0, padx=80, pady=(0, 20), sticky="ew")
        self._summary_card.grid_columnconfigure(0, weight=1)

        self._summary_label = customtkinter.CTkLabel(
            self._summary_card,
            text="",
            font=FONTS["body"],
            text_color=COLORS["fg"],
            justify="left",
            anchor="w",
            wraplength=500,
        )
        self._summary_label.pack(padx=24, pady=20, fill="x")

        # Primary action
        btn_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        btn_frame.grid(row=4, column=0, pady=(0, 12))

        self._open_btn = customtkinter.CTkButton(
            btn_frame,
            text=f"{ICONS['folder']}  Open Output Folder",
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["button_text"],
            corner_radius=12,
            height=48,
            width=240,
            command=self._open_folder,
        )
        self._open_btn.pack(side="left", padx=8)

        # Secondary actions
        secondary_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        secondary_frame.grid(row=5, column=0, pady=(0, 8))

        customtkinter.CTkButton(
            secondary_frame,
            text="Export Again",
            font=FONTS["label"],
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["accent"],
            border_width=1,
            border_color=COLORS["accent"],
            corner_radius=8,
            height=40,
            width=140,
            command=self._export_again,
        ).pack(side="left", padx=8)

        customtkinter.CTkButton(
            secondary_frame,
            text="Exit",
            font=FONTS["label"],
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["subtle"],
            border_width=1,
            border_color=COLORS["subtle"],
            corner_radius=8,
            height=40,
            width=140,
            command=self._exit_app,
        ).pack(side="left", padx=8)

    def on_show(self) -> None:
        """Called when this screen becomes visible."""
        self._populate_summary()
        self.after(300, lambda: self._celebrate(0))

    def _populate_summary(self) -> None:
        state = self._app.wizard_state
        total = state.get("total_emails", 0)
        results: list[ExportResult] = state.get("results", [])
        output_dir = state.get("output_dir", "")

        lines = [f"Total emails exported: {total:,}"]

        if results:
            format_names = [r.format_name for r in results if r.success]
            if format_names:
                lines.append(f"Formats: {', '.join(format_names)}")
            for r in results:
                status = ICONS["complete"] if r.success else ICONS["error"]
                lines.append(f"  {status}  {r.format_name}: {r.file_path}")
                if r.error:
                    lines.append(f"       Error: {r.error}")

        if output_dir:
            lines.append(f"\nSaved to: {output_dir}")

        self._summary_label.configure(text="\n".join(lines))

    def _open_folder(self) -> None:
        output_dir = self._app.wizard_state.get("output_dir", "")
        if not output_dir or not os.path.isdir(output_dir):
            return
        system = platform.system()
        if system == "Windows":
            os.startfile(output_dir)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", output_dir])  # noqa: S603, S607
        else:
            subprocess.Popen(["xdg-open", output_dir])  # noqa: S603, S607

    def _export_again(self) -> None:
        self._app.go_to_screen("Folders")

    def _exit_app(self) -> None:
        client = self._app.wizard_state.get("client")
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
        self._app.destroy()

    # -- Celebration animation (no canvas overlay) --------------------------

    def _celebrate(self, step: int) -> None:
        """Cycle the checkmark icon through celebration colors, then settle."""
        if step >= len(_CELEBRATION_COLORS) * 2:
            self._icon.configure(text_color=COLORS["success"])
            return
        color = _CELEBRATION_COLORS[step % len(_CELEBRATION_COLORS)]
        self._icon.configure(text_color=color)
        self.after(120, self._celebrate, step + 1)
