# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from aol_email_exporter.ui.theme import COLORS, FONTS, ICONS, fade_in

if TYPE_CHECKING:
    from aol_email_exporter.ui.app import AOLExporterApp


class WelcomeScreen(customtkinter.CTkFrame):
    """First wizard screen — introduces the app and invites the user to begin."""

    def __init__(self, parent: customtkinter.CTkFrame, app: AOLExporterApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._build()

    def _build(self) -> None:
        # Spacer to push content toward vertical center
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=2)
        self.grid_columnconfigure(0, weight=1)

        # Envelope icon
        self._icon = customtkinter.CTkLabel(
            self,
            text=ICONS["welcome"],
            font=FONTS["icon_large"],
            text_color=COLORS["accent"],
        )
        self._icon.grid(row=1, column=0, pady=(0, 8))

        # Title
        self._title = customtkinter.CTkLabel(
            self,
            text="AOL Email Exporter",
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["fg"],
        )
        self._title.grid(row=2, column=0, pady=(0, 4))

        # Subtitle
        self._subtitle = customtkinter.CTkLabel(
            self,
            text="Save your emails safely to your computer",
            font=FONTS["body"],
            text_color=COLORS["subtle"],
        )
        self._subtitle.grid(row=3, column=0, pady=(0, 24))

        # Feature bullets
        features = [
            f"{ICONS['welcome']}  Download emails from AOL",
            f"{ICONS['filter']}  Filter by date, sender, or subject",
            f"{ICONS['format']}  Save as PDF, Excel, or CSV",
        ]
        self._bullet_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        self._bullet_frame.grid(row=4, column=0, pady=(0, 32))

        self._bullet_labels: list[customtkinter.CTkLabel] = []
        for i, text in enumerate(features):
            lbl = customtkinter.CTkLabel(
                self._bullet_frame,
                text=text,
                font=FONTS["body"],
                text_color=COLORS["fg"],
                anchor="w",
            )
            lbl.grid(row=i, column=0, sticky="w", padx=40, pady=4)
            self._bullet_labels.append(lbl)

        # Get Started button
        self._start_btn = customtkinter.CTkButton(
            self,
            text="Get Started  " + ICONS["next"],
            font=FONTS["button"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=12,
            height=50,
            width=240,
            command=self._on_get_started,
        )
        self._start_btn.grid(row=5, column=0, pady=(0, 24))

        # Version text
        from aol_email_exporter import __version__

        self._version = customtkinter.CTkLabel(
            self,
            text=f"Version {__version__}",
            font=FONTS["small"],
            text_color=COLORS["subtle"],
        )
        self._version.grid(row=6, column=0, pady=(8, 0))

    def on_show(self) -> None:
        """Called when this screen becomes visible. Trigger staggered fade-in."""
        elements = [
            self._icon,
            self._title,
            self._subtitle,
            self._bullet_frame,
            self._start_btn,
            self._version,
        ]
        for i, widget in enumerate(elements):
            self.after(150 * i, lambda w=widget: fade_in(w, steps=10, delay_ms=30))

    def _on_get_started(self) -> None:
        self._app.go_next()
