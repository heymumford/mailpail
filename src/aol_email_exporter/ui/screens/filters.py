# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import customtkinter

from aol_email_exporter.models import FilterParams
from aol_email_exporter.ui.theme import COLORS, FONTS, ICONS, fade_in

if TYPE_CHECKING:
    from aol_email_exporter.ui.app import AOLExporterApp


class FilterScreen(customtkinter.CTkFrame):
    """Wizard step 4 — optional email filters (dates, sender, subject, unread)."""

    def __init__(self, parent: customtkinter.CTkFrame, app: AOLExporterApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=2)

        # Header
        header_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        header_frame.grid(row=1, column=0, pady=(0, 4))

        customtkinter.CTkLabel(
            header_frame,
            text=ICONS["filter"],
            font=FONTS["icon"],
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 12))

        customtkinter.CTkLabel(
            header_frame,
            text="Filter Emails (Optional)",
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["fg"],
        ).pack(side="left")

        # Subtitle
        customtkinter.CTkLabel(
            self,
            text="Leave blank to download everything",
            font=FONTS["body"],
            text_color=COLORS["subtle"],
        ).grid(row=2, column=0, pady=(0, 16))

        # Form card
        form_card = customtkinter.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        form_card.grid(row=3, column=0, padx=60, sticky="ew")
        form_card.grid_columnconfigure(1, weight=1)
        form_card.grid_columnconfigure(3, weight=1)

        # Date range row
        customtkinter.CTkLabel(
            form_card,
            text="Date Range",
            font=(FONTS["label"][0], FONTS["label"][1], "bold"),
            text_color=COLORS["fg"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, padx=24, pady=(20, 8), sticky="w")

        customtkinter.CTkLabel(
            form_card,
            text="From:",
            font=FONTS["label"],
            text_color=COLORS["fg"],
        ).grid(row=1, column=0, padx=(24, 8), pady=4, sticky="e")

        self._date_from = customtkinter.CTkEntry(
            form_card,
            placeholder_text="YYYY-MM-DD",
            font=FONTS["label"],
            height=38,
            corner_radius=8,
        )
        self._date_from.grid(row=1, column=1, padx=(0, 16), pady=4, sticky="ew")

        customtkinter.CTkLabel(
            form_card,
            text="To:",
            font=FONTS["label"],
            text_color=COLORS["fg"],
        ).grid(row=1, column=2, padx=(0, 8), pady=4, sticky="e")

        self._date_to = customtkinter.CTkEntry(
            form_card,
            placeholder_text="YYYY-MM-DD",
            font=FONTS["label"],
            height=38,
            corner_radius=8,
        )
        self._date_to.grid(row=1, column=3, padx=(0, 24), pady=4, sticky="ew")

        # Sender filter
        customtkinter.CTkLabel(
            form_card,
            text="Sender",
            font=(FONTS["label"][0], FONTS["label"][1], "bold"),
            text_color=COLORS["fg"],
            anchor="w",
        ).grid(row=2, column=0, columnspan=4, padx=24, pady=(16, 4), sticky="w")

        self._sender_entry = customtkinter.CTkEntry(
            form_card,
            placeholder_text="Filter by sender email",
            font=FONTS["label"],
            height=38,
            corner_radius=8,
        )
        self._sender_entry.grid(row=3, column=0, columnspan=4, padx=24, pady=(0, 8), sticky="ew")

        # Subject filter
        customtkinter.CTkLabel(
            form_card,
            text="Subject",
            font=(FONTS["label"][0], FONTS["label"][1], "bold"),
            text_color=COLORS["fg"],
            anchor="w",
        ).grid(row=4, column=0, columnspan=4, padx=24, pady=(8, 4), sticky="w")

        self._subject_entry = customtkinter.CTkEntry(
            form_card,
            placeholder_text="Filter by subject keyword",
            font=FONTS["label"],
            height=38,
            corner_radius=8,
        )
        self._subject_entry.grid(row=5, column=0, columnspan=4, padx=24, pady=(0, 12), sticky="ew")

        # Unread only checkbox
        self._unread_var = customtkinter.StringVar(value="off")
        self._unread_cb = customtkinter.CTkCheckBox(
            form_card,
            text="  Unread emails only",
            font=FONTS["label"],
            text_color=COLORS["fg"],
            variable=self._unread_var,
            onvalue="on",
            offvalue="off",
            corner_radius=4,
            checkbox_width=24,
            checkbox_height=24,
        )
        self._unread_cb.grid(row=6, column=0, columnspan=4, padx=24, pady=(4, 20), sticky="w")

        # Skip Filters button (secondary, next to standard nav)
        self._skip_btn = customtkinter.CTkButton(
            self,
            text="Skip Filters",
            font=FONTS["label"],
            fg_color="transparent",
            hover_color="#E0E4EA",
            text_color=COLORS["subtle"],
            border_width=1,
            border_color=COLORS["subtle"],
            corner_radius=8,
            height=36,
            width=140,
            command=self._skip_filters,
        )
        self._skip_btn.grid(row=4, column=0, pady=(12, 0))

    def on_show(self) -> None:
        """Called when this screen becomes visible."""
        fade_in(self, steps=10, delay_ms=30)

    def _skip_filters(self) -> None:
        """Skip all filters and advance to next screen."""
        self._app.wizard_state["filters"] = FilterParams()
        self._app.go_next()

    def _parse_date(self, value: str) -> datetime.date | None:
        """Parse a YYYY-MM-DD string, returning None on failure."""
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return None

    def build_filters(self) -> FilterParams:
        """Construct FilterParams from the current form state."""
        return FilterParams(
            date_from=self._parse_date(self._date_from.get()),
            date_to=self._parse_date(self._date_to.get()),
            sender=self._sender_entry.get().strip() or None,
            subject=self._subject_entry.get().strip() or None,
            unread_only=self._unread_var.get() == "on",
        )

    def validate(self) -> bool:
        """Filters are always valid (all optional). Store them in wizard state."""
        # Validate date format if provided
        date_from_text = self._date_from.get().strip()
        date_to_text = self._date_to.get().strip()

        if date_from_text and self._parse_date(date_from_text) is None:
            return False
        if date_to_text and self._parse_date(date_to_text) is None:
            return False

        self._app.wizard_state["filters"] = self.build_filters()
        return True
