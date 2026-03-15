# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import platform
import random
import subprocess
import sys
from typing import TYPE_CHECKING

import customtkinter

from aol_email_exporter.ui.theme import COLORS, FONTS, ICONS, fade_in

if TYPE_CHECKING:
    from aol_email_exporter.models import ExportResult
    from aol_email_exporter.ui.app import AOLExporterApp


class CompleteScreen(customtkinter.CTkFrame):
    """Wizard step 7 — export summary, file locations, and celebratory finish."""

    def __init__(self, parent: customtkinter.CTkFrame, app: AOLExporterApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._confetti_ids: list[int] = []
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

        # Action buttons
        btn_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        btn_frame.grid(row=4, column=0, pady=(0, 12))

        self._open_btn = customtkinter.CTkButton(
            btn_frame,
            text=f"{ICONS['folder']}  Open Output Folder",
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=12,
            height=48,
            width=240,
            command=self._open_folder,
        )
        self._open_btn.pack(side="left", padx=8)

        # Secondary buttons row
        secondary_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        secondary_frame.grid(row=5, column=0, pady=(0, 8))

        customtkinter.CTkButton(
            secondary_frame,
            text="Export Again",
            font=FONTS["label"],
            fg_color="transparent",
            hover_color="#E0E4EA",
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
            hover_color="#E0E4EA",
            text_color=COLORS["subtle"],
            border_width=1,
            border_color=COLORS["subtle"],
            corner_radius=8,
            height=40,
            width=140,
            command=self._exit_app,
        ).pack(side="left", padx=8)

        # Canvas for confetti overlay
        import tkinter as tk

        self._canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        self._canvas.grid(row=0, column=0, rowspan=8, sticky="nsew")
        self._canvas.lower()

    def on_show(self) -> None:
        """Called when this screen becomes visible. Populate summary and celebrate."""
        self._populate_summary()
        fade_in(self, steps=10, delay_ms=30)
        self.after(300, self._start_confetti)

    def _populate_summary(self) -> None:
        """Fill the summary card with export results."""
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
        """Open the output directory in the system file manager."""
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
        """Return to the folders screen for another export."""
        self._app.go_to_screen("Folders")

    def _exit_app(self) -> None:
        """Close the application."""
        # Disconnect client if still connected
        client = self._app.wizard_state.get("client")
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
        self._app.destroy()

    # -- Confetti animation ------------------------------------------------

    _CONFETTI_COLORS = ["#4A90D9", "#27AE60", "#F39C12", "#E74C3C", "#9B59B6", "#1ABC9C"]

    def _start_confetti(self) -> None:
        """Spawn confetti dots that fall and fade."""
        self._canvas.lift()
        for _ in range(40):
            self.after(random.randint(0, 600), self._spawn_dot)
        # Lower canvas after confetti finishes
        self.after(3000, self._canvas.lower)

    def _spawn_dot(self) -> None:
        """Create a single confetti dot and animate it."""
        try:
            w = self._canvas.winfo_width()
        except Exception:
            return
        if w < 10:
            w = 600

        x = random.randint(20, max(w - 20, 21))
        y = random.randint(-20, 0)
        size = random.randint(4, 10)
        color = random.choice(self._CONFETTI_COLORS)

        dot_id = self._canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")
        self._confetti_ids.append(dot_id)
        self._animate_dot(dot_id, x, y, size, speed=random.uniform(1.5, 4.0), step=0)

    def _animate_dot(self, dot_id: int, x: float, y: float, size: int, speed: float, step: int) -> None:
        """Move a dot downward and fade it out."""
        if step > 60:
            try:
                self._canvas.delete(dot_id)
            except Exception:
                pass
            return

        new_y = y + speed * step
        drift = random.uniform(-1, 1)
        try:
            self._canvas.coords(dot_id, x + drift, new_y, x + drift + size, new_y + size)
        except Exception:
            return

        # Fade by reducing alpha (simulate with lighter colors near the end)
        if step > 40:
            try:
                self._canvas.itemconfigure(dot_id, stipple="gray25")
            except Exception:
                pass

        self.after(30, self._animate_dot, dot_id, x + drift, new_y, size, speed, step + 1)
