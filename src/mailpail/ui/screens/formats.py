# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter

from mailpail.ui.theme import COLORS, FONTS, ICONS

if TYPE_CHECKING:
    from mailpail.ui.app import MailpailApp

_FORMAT_OPTIONS: list[dict[str, str]] = [
    {
        "key": "csv",
        "icon": "\U0001f4ca",
        "title": "Compressed CSV",
        "description": "Small file, great for data analysis",
    },
    {
        "key": "excel",
        "icon": "\U0001f4ca",
        "title": "Excel Spreadsheet",
        "description": "One sheet with all emails",
    },
    {
        "key": "excel-sheets",
        "icon": "\U0001f4da",
        "title": "Excel with Tabs",
        "description": "Emails organized by folder",
    },
    {
        "key": "pdf",
        "icon": "\U0001f4d1",
        "title": "PDF Document",
        "description": "Easy to read and share",
    },
]


class FormatScreen(customtkinter.CTkFrame):
    """Wizard step 5 — choose export formats and output directory."""

    def __init__(self, parent: customtkinter.CTkFrame, app: MailpailApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._format_vars: dict[str, customtkinter.StringVar] = {}
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=2)

        # Header
        header_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        header_frame.grid(row=1, column=0, pady=(0, 4))

        customtkinter.CTkLabel(
            header_frame,
            text=ICONS["format"],
            font=FONTS["icon"],
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 12))

        customtkinter.CTkLabel(
            header_frame,
            text="Choose Export Formats",
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["fg"],
        ).pack(side="left")

        # Format cards container
        cards_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        cards_frame.grid(row=2, column=0, padx=40, pady=(8, 16), sticky="ew")
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        for i, fmt in enumerate(_FORMAT_OPTIONS):
            row = i // 2
            col = i % 2
            card = self._build_format_card(cards_frame, fmt)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="ew")

        # Output directory
        dir_frame = customtkinter.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        dir_frame.grid(row=3, column=0, padx=60, pady=(0, 8), sticky="ew")
        dir_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            dir_frame,
            text="Save to:",
            font=(FONTS["label"][0], FONTS["label"][1], "bold"),
            text_color=COLORS["fg"],
        ).grid(row=0, column=0, padx=(20, 8), pady=16, sticky="w")

        default_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Mailpail_Export")
        self._dir_entry = customtkinter.CTkEntry(
            dir_frame,
            font=FONTS["label"],
            height=38,
            corner_radius=8,
        )
        self._dir_entry.insert(0, default_dir)
        self._dir_entry.grid(row=0, column=1, padx=(0, 8), pady=16, sticky="ew")

        customtkinter.CTkButton(
            dir_frame,
            text="Browse",
            font=FONTS["label"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["button_text"],
            corner_radius=8,
            height=38,
            width=100,
            command=self._browse_directory,
        ).grid(row=0, column=2, padx=(0, 20), pady=16)

    def _build_format_card(self, parent: customtkinter.CTkFrame, fmt: dict[str, str]) -> customtkinter.CTkFrame:
        """Build a single format selection card."""
        card = customtkinter.CTkFrame(
            parent,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid_columnconfigure(0, weight=1)

        # Default CSV to checked
        default_val = "on" if fmt["key"] == "csv" else "off"
        var = customtkinter.StringVar(value=default_val)
        self._format_vars[fmt["key"]] = var

        cb = customtkinter.CTkCheckBox(
            card,
            text=f"  {fmt['icon']}  {fmt['title']}",
            font=FONTS["body"],
            text_color=COLORS["fg"],
            variable=var,
            onvalue="on",
            offvalue="off",
            corner_radius=4,
            checkbox_width=24,
            checkbox_height=24,
        )
        cb.grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        customtkinter.CTkLabel(
            card,
            text=fmt["description"],
            font=FONTS["small"],
            text_color=COLORS["subtle"],
            anchor="w",
        ).grid(row=1, column=0, padx=(60, 16), pady=(0, 16), sticky="w")

        return card

    def _browse_directory(self) -> None:
        """Open a directory chooser dialog."""
        path = filedialog.askdirectory(
            title="Choose Export Folder",
            initialdir=os.path.expanduser("~"),
        )
        if path:
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, path)

    def on_show(self) -> None:
        """Called when this screen becomes visible."""

    def get_selected_formats(self) -> list[str]:
        """Return list of selected format keys."""
        return [key for key, var in self._format_vars.items() if var.get() == "on"]

    def get_output_dir(self) -> str:
        """Return the output directory path."""
        return self._dir_entry.get().strip()

    def validate(self) -> bool:
        """At least one format must be selected and output dir must be set."""
        formats = self.get_selected_formats()
        output_dir = self.get_output_dir()

        if not formats:
            return False
        if not output_dir:
            return False

        self._app.wizard_state["formats"] = formats
        self._app.wizard_state["output_dir"] = output_dir
        return True
