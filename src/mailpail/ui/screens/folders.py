# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import customtkinter

from mailpail.ui.theme import COLORS, FONTS, ICONS

if TYPE_CHECKING:
    from mailpail.ui.app import MailpailApp


class FolderScreen(customtkinter.CTkFrame):
    """Wizard step 3 — select which IMAP folders to export."""

    def __init__(self, parent: customtkinter.CTkFrame, app: MailpailApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._checkboxes: list[tuple[customtkinter.CTkCheckBox, customtkinter.StringVar]] = []
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
            text=ICONS["folder"],
            font=FONTS["icon"],
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 12))

        customtkinter.CTkLabel(
            header_frame,
            text="Choose Folders",
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["fg"],
        ).pack(side="left")

        # Subtitle
        customtkinter.CTkLabel(
            self,
            text="Select which folders to download",
            font=FONTS["body"],
            text_color=COLORS["subtle"],
        ).grid(row=2, column=0, pady=(0, 16))

        # Select All / Deselect All buttons
        btn_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        btn_frame.grid(row=3, column=0, pady=(0, 8))

        customtkinter.CTkButton(
            btn_frame,
            text="Select All",
            font=FONTS["label"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["button_text"],
            corner_radius=8,
            height=32,
            width=120,
            command=self._select_all,
        ).pack(side="left", padx=(0, 8))

        customtkinter.CTkButton(
            btn_frame,
            text="Deselect All",
            font=FONTS["label"],
            fg_color=COLORS["subtle"],
            hover_color=COLORS["subtle_hover"],
            text_color=COLORS["button_text"],
            corner_radius=8,
            height=32,
            width=120,
            command=self._deselect_all,
        ).pack(side="left")

        # Scrollable folder list
        self._scroll_frame = customtkinter.CTkScrollableFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            height=280,
        )
        self._scroll_frame.grid(row=4, column=0, padx=60, pady=(0, 8), sticky="ew")
        self._scroll_frame.grid_columnconfigure(0, weight=1)

        # Loading label (shown while fetching folders)
        self._loading_label = customtkinter.CTkLabel(
            self._scroll_frame,
            text="Loading folders...",
            font=FONTS["body"],
            text_color=COLORS["subtle"],
        )
        self._loading_label.grid(row=0, column=0, padx=20, pady=20)

    def on_show(self) -> None:
        """Called when this screen becomes visible. Load folders from server."""
        self._load_folders()

    def _load_folders(self) -> None:
        """Fetch folder list from the IMAP client in a background thread."""
        client = self._app.wizard_state.get("client")
        if client is None:
            self._loading_label.configure(
                text=f"{ICONS['error']} No connection. Go back and sign in.",
                text_color=COLORS["error"],
            )
            return

        self._loading_label.configure(text="Loading folders...", text_color=COLORS["subtle"])
        thread = threading.Thread(target=self._fetch_folders, args=(client,), daemon=True)
        thread.start()

    def _fetch_folders(self, client: object) -> None:
        """Run the folder fetch off the main thread."""
        try:
            folders = client.list_folders()  # type: ignore[union-attr]
            self._app.run_on_main(self._populate_folders, folders)
        except Exception as exc:
            self._app.run_on_main(self._on_folder_error, str(exc))

    def _populate_folders(self, folders: list[str]) -> None:
        """Build checkboxes for each folder (runs on main thread)."""
        # Clear existing
        self._loading_label.grid_forget()
        for cb, _var in self._checkboxes:
            cb.destroy()
        self._checkboxes.clear()

        if not folders:
            customtkinter.CTkLabel(
                self._scroll_frame,
                text="No folders found.",
                font=FONTS["body"],
                text_color=COLORS["subtle"],
            ).grid(row=0, column=0, padx=20, pady=20)
            return

        for i, folder_name in enumerate(sorted(folders)):
            var = customtkinter.StringVar(value="on" if folder_name == "INBOX" else "off")
            cb = customtkinter.CTkCheckBox(
                self._scroll_frame,
                text=f"  {ICONS['folder']}  {folder_name}",
                font=FONTS["body"],
                text_color=COLORS["fg"],
                variable=var,
                onvalue="on",
                offvalue="off",
                corner_radius=4,
                height=36,
                checkbox_width=24,
                checkbox_height=24,
            )
            cb.grid(row=i, column=0, padx=20, pady=4, sticky="w")
            self._checkboxes.append((cb, var))

    def _on_folder_error(self, error_msg: str) -> None:
        """Show folder loading error."""
        self._loading_label.configure(
            text=f"{ICONS['error']} Failed to load folders: {error_msg}",
            text_color=COLORS["error"],
        )

    def _select_all(self) -> None:
        for _cb, var in self._checkboxes:
            var.set("on")

    def _deselect_all(self) -> None:
        for _cb, var in self._checkboxes:
            var.set("off")

    def get_selected_folders(self) -> list[str]:
        """Return list of selected folder names."""
        selected = []
        for cb, var in self._checkboxes:
            if var.get() == "on":
                # Extract folder name from label text (strip icon prefix)
                text = cb.cget("text").strip()
                # Remove the folder icon prefix
                if ICONS["folder"] in text:
                    text = text.split(ICONS["folder"], 1)[1].strip()
                selected.append(text)
        return selected

    def validate(self) -> bool:
        """At least one folder must be selected."""
        selected = self.get_selected_folders()
        if not selected:
            return False
        self._app.wizard_state["selected_folders"] = selected
        return True
