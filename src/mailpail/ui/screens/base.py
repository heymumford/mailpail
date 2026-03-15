# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""BaseScreen — standard skeleton for all wizard screens.

Provides a consistent layout: header row (icon + title), subtitle,
card frame, and action row. All screens inherit from this class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from mailpail.ui.theme import COLORS, FONTS

if TYPE_CHECKING:
    from mailpail.ui.app import MailpailApp


class BaseScreen(customtkinter.CTkFrame):
    """Standard wizard screen skeleton.

    Subclasses override ``_build_content`` to populate the card area
    and optionally ``on_show``, ``validate``, etc.
    """

    # Subclasses set these to customize the header.
    screen_icon: str = ""
    screen_title: str = ""
    screen_subtitle: str = ""

    def __init__(self, parent: customtkinter.CTkFrame, app: MailpailApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(10, weight=2)

        self._build_header()
        self._build_content()

    def _build_header(self) -> None:
        """Render icon + title row and subtitle."""
        if self.screen_icon or self.screen_title:
            header_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
            header_frame.grid(row=1, column=0, pady=(0, 4))

            if self.screen_icon:
                customtkinter.CTkLabel(
                    header_frame,
                    text=self.screen_icon,
                    font=FONTS["icon"],
                    text_color=COLORS["accent"],
                ).pack(side="left", padx=(0, 12))

            if self.screen_title:
                customtkinter.CTkLabel(
                    header_frame,
                    text=self.screen_title,
                    font=(FONTS["header"][0], FONTS["header"][1], "bold"),
                    text_color=COLORS["fg"],
                ).pack(side="left")

        if self.screen_subtitle:
            customtkinter.CTkLabel(
                self,
                text=self.screen_subtitle,
                font=FONTS["body"],
                text_color=COLORS["subtle"],
            ).grid(row=2, column=0, pady=(0, 16))

    def _build_content(self) -> None:
        """Override in subclasses to build the screen body."""

    def on_show(self) -> None:
        """Called when the screen becomes visible. Override as needed."""

    def make_card(self, row: int = 3, padx: int = 60) -> customtkinter.CTkFrame:
        """Create a standard white card frame at the given grid row."""
        card = customtkinter.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=row, column=0, padx=padx, sticky="ew")
        return card
