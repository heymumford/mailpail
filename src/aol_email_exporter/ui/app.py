# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import platform
import tkinter as tk
import webbrowser
from typing import Any

import customtkinter

from aol_email_exporter.ui.theme import (
    ACCEL_PREFIX,
    COLORS,
    FONTS,
    ICONS,
    WIZARD_STEPS,
)
from aol_email_exporter.ui.screens.complete import CompleteScreen
from aol_email_exporter.ui.screens.filters import FilterScreen
from aol_email_exporter.ui.screens.folders import FolderScreen
from aol_email_exporter.ui.screens.formats import FormatScreen
from aol_email_exporter.ui.screens.login import LoginScreen
from aol_email_exporter.ui.screens.progress import ProgressScreen
from aol_email_exporter.ui.screens.welcome import WelcomeScreen

_SYSTEM = platform.system()
_APP_NAME = "AOL Email Exporter"


class AOLExporterApp(customtkinter.CTk):
    """Main wizard application window."""

    def __init__(self) -> None:
        super().__init__()

        # Window configuration
        self.title(_APP_NAME)
        self.geometry("800x600")
        self.minsize(700, 500)
        self._center_window(800, 600)

        customtkinter.set_appearance_mode("light")
        customtkinter.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg"])

        # Shared state between wizard screens
        self.wizard_state: dict[str, Any] = {}
        self._current_step = 0

        # Platform-native menu bar
        self._build_menu_bar()

        # Layout
        self._build_layout()
        self._build_screens()
        self._show_screen_at_index(0)

    # -- Platform-native menu bar -------------------------------------------

    def _build_menu_bar(self) -> None:
        menubar = tk.Menu(self)
        self.configure(menu=menubar)

        mod = "Command" if _SYSTEM == "Darwin" else "Control"

        # macOS: register app-menu handlers (About, Preferences, Quit)
        if _SYSTEM == "Darwin":
            try:
                self.createcommand("tk::mac::ShowPreferences", self._show_preferences)
                self.createcommand("::tk::mac::Quit", self._quit_app)
            except Exception:
                pass
            # macOS Help menu (appears at the right end of the menu bar)
            self.createcommand("::tk::mac::ShowHelp", self._show_help)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="New Export\u2026",
            accelerator=f"{ACCEL_PREFIX}+N",
            command=self._new_export,
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Open Export Folder",
            accelerator=f"{ACCEL_PREFIX}+O",
            command=self._open_export_folder,
        )
        if _SYSTEM != "Darwin":
            file_menu.add_separator()
            file_menu.add_command(label="Exit", accelerator="Alt+F4", command=self._quit_app)

        # Keyboard bindings for File menu
        self.bind_all(f"<{mod}-n>", lambda _e: self._new_export())
        self.bind_all(f"<{mod}-o>", lambda _e: self._open_export_folder())

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", accelerator=f"{ACCEL_PREFIX}+X")
        edit_menu.add_command(label="Copy", accelerator=f"{ACCEL_PREFIX}+C")
        edit_menu.add_command(label="Paste", accelerator=f"{ACCEL_PREFIX}+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", accelerator=f"{ACCEL_PREFIX}+A")

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Go to Welcome", command=lambda: self.go_to_screen("Welcome"))
        view_menu.add_command(label="Go to Login", command=lambda: self.go_to_screen("Login"))
        view_menu.add_separator()
        view_menu.add_command(
            label="Reset Wizard",
            accelerator=f"{ACCEL_PREFIX}+R",
            command=self._reset_wizard,
        )
        self.bind_all(f"<{mod}-r>", lambda _e: self._reset_wizard())

        # Session menu
        session_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Session", menu=session_menu)
        session_menu.add_command(label="Test Connection\u2026", command=self._menu_test_connection)
        session_menu.add_command(label="List Folders", command=self._menu_list_folders)
        session_menu.add_separator()
        session_menu.add_command(label="Disconnect", command=self._menu_disconnect)

        # Help menu (on non-macOS; macOS uses the built-in Help menu position)
        if _SYSTEM != "Darwin":
            help_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Help", menu=help_menu)
            help_menu.add_command(label=f"About {_APP_NAME}", command=self._show_about)
            help_menu.add_command(label="AOL App Password Help", command=self._open_aol_help)
            help_menu.add_separator()
            help_menu.add_command(
                label="GitHub Repository",
                command=lambda: webbrowser.open("https://github.com/heymumford/aol-email-exporter"),
            )

    # -- Menu actions -------------------------------------------------------

    def _show_preferences(self) -> None:
        pass  # placeholder for future settings dialog

    def _show_help(self) -> None:
        webbrowser.open("https://github.com/heymumford/aol-email-exporter")

    def _show_about(self) -> None:
        from aol_email_exporter import __version__

        about = customtkinter.CTkToplevel(self)
        about.title(f"About {_APP_NAME}")
        about.geometry("360x220")
        about.resizable(False, False)
        about.transient(self)
        about.grab_set()

        customtkinter.CTkLabel(
            about, text=ICONS["welcome"], font=FONTS["icon"]
        ).pack(pady=(20, 4))
        customtkinter.CTkLabel(
            about, text=_APP_NAME, font=(FONTS["subheader"][0], FONTS["subheader"][1], "bold")
        ).pack()
        customtkinter.CTkLabel(
            about, text=f"Version {__version__}", font=FONTS["small"], text_color=COLORS["subtle"]
        ).pack(pady=(2, 4))
        customtkinter.CTkLabel(
            about,
            text="\u00A9 2026+ Eric C. Mumford",
            font=FONTS["small"],
            text_color=COLORS["subtle"],
        ).pack()
        customtkinter.CTkLabel(
            about, text="Licensed under GPL-3.0", font=FONTS["small"], text_color=COLORS["subtle"]
        ).pack(pady=(0, 8))
        customtkinter.CTkButton(about, text="OK", width=80, command=about.destroy).pack(pady=(0, 16))

    def _open_aol_help(self) -> None:
        webbrowser.open("https://login.aol.com/account/security/app-passwords")

    def _new_export(self) -> None:
        self._reset_wizard()

    def _open_export_folder(self) -> None:
        import os
        import subprocess

        output_dir = self.wizard_state.get("output_dir", "")
        if not output_dir or not os.path.isdir(output_dir):
            return
        if _SYSTEM == "Windows":
            os.startfile(output_dir)  # type: ignore[attr-defined]
        elif _SYSTEM == "Darwin":
            subprocess.Popen(["open", output_dir])  # noqa: S603, S607
        else:
            subprocess.Popen(["xdg-open", output_dir])  # noqa: S603, S607

    def _reset_wizard(self) -> None:
        client = self.wizard_state.get("client")
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
        self.wizard_state.clear()
        self._show_screen_at_index(0)

    def _menu_test_connection(self) -> None:
        self.go_to_screen("Login")

    def _menu_list_folders(self) -> None:
        if self.wizard_state.get("client"):
            self.go_to_screen("Folders")
        else:
            self.go_to_screen("Login")

    def _menu_disconnect(self) -> None:
        client = self.wizard_state.get("client")
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
            self.wizard_state.pop("client", None)

    def _quit_app(self) -> None:
        self._menu_disconnect()
        self.destroy()

    # -- Window layout ------------------------------------------------------

    def _center_window(self, width: int, height: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top bar — progress dots
        self._top_bar = customtkinter.CTkFrame(self, fg_color=COLORS["bg"], height=40)
        self._top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(12, 0))
        self._top_bar.grid_propagate(False)
        self._dot_labels: list[customtkinter.CTkLabel] = []
        self._build_progress_dots()

        # Main content area
        self._content_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        self._content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_rowconfigure(0, weight=1)

        # Bottom nav bar
        self._nav_bar = customtkinter.CTkFrame(self, fg_color=COLORS["bg"], height=60)
        self._nav_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
        self._nav_bar.grid_propagate(False)
        self._nav_bar.grid_columnconfigure(1, weight=1)

        self._back_btn = customtkinter.CTkButton(
            self._nav_bar,
            text=f"{ICONS['back']}  Back",
            font=FONTS["body"],
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["subtle"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
            height=44,
            width=120,
            command=self.go_back,
        )
        self._back_btn.grid(row=0, column=0, padx=(20, 0), pady=8, sticky="w")

        self._next_btn = customtkinter.CTkButton(
            self._nav_bar,
            text=f"Next  {ICONS['next']}",
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=10,
            height=44,
            width=120,
            command=self.go_next,
        )
        self._next_btn.grid(row=0, column=2, padx=(0, 20), pady=8, sticky="e")

    def _build_progress_dots(self) -> None:
        inner = customtkinter.CTkFrame(self._top_bar, fg_color=COLORS["bg"])
        inner.place(relx=0.5, rely=0.5, anchor="center")

        for i, _step_name in enumerate(WIZARD_STEPS):
            dot_frame = customtkinter.CTkFrame(inner, fg_color=COLORS["bg"])
            dot_frame.pack(side="left", padx=4)

            dot = customtkinter.CTkLabel(
                dot_frame, text="\u25CF", font=FONTS["dot"], text_color=COLORS["subtle"], width=20
            )
            dot.pack()
            self._dot_labels.append(dot)

            if i < len(WIZARD_STEPS) - 1:
                customtkinter.CTkLabel(
                    inner, text="\u2500\u2500", font=FONTS["connector"], text_color=COLORS["border"], width=20
                ).pack(side="left", padx=0)

    def _update_progress_dots(self) -> None:
        for i, dot in enumerate(self._dot_labels):
            if i < self._current_step:
                dot.configure(text_color=COLORS["success"])
            elif i == self._current_step:
                dot.configure(text_color=COLORS["accent"])
            else:
                dot.configure(text_color=COLORS["subtle"])

    # -- Screen management --------------------------------------------------

    def _build_screens(self) -> None:
        self._screens: dict[str, customtkinter.CTkFrame] = {
            "Welcome": WelcomeScreen(self._content_frame, self),
            "Login": LoginScreen(self._content_frame, self),
            "Folders": FolderScreen(self._content_frame, self),
            "Filters": FilterScreen(self._content_frame, self),
            "Format": FormatScreen(self._content_frame, self),
            "Download": ProgressScreen(self._content_frame, self),
            "Complete": CompleteScreen(self._content_frame, self),
        }

    def _show_screen_at_index(self, index: int) -> None:
        self._current_step = index
        step_name = WIZARD_STEPS[index]

        for screen in self._screens.values():
            screen.grid_forget()

        screen = self._screens[step_name]
        screen.grid(row=0, column=0, sticky="nsew")

        self._update_nav_buttons()
        self._update_progress_dots()

        if hasattr(screen, "on_show"):
            screen.on_show()

    def _update_nav_buttons(self) -> None:
        step_name = WIZARD_STEPS[self._current_step]

        if step_name == "Welcome":
            self._back_btn.grid_forget()
            self._next_btn.grid_forget()
        elif step_name == "Complete":
            self._back_btn.grid_forget()
            self._next_btn.grid_forget()
        elif step_name == "Download":
            self._back_btn.grid(row=0, column=0, padx=(20, 0), pady=8, sticky="w")
            self._back_btn.configure(state="disabled")
            self._next_btn.grid_forget()
        else:
            self._back_btn.grid(row=0, column=0, padx=(20, 0), pady=8, sticky="w")
            self._back_btn.configure(state="normal")
            self._next_btn.grid(row=0, column=2, padx=(0, 20), pady=8, sticky="e")
            self._next_btn.configure(state="normal")

            if step_name == "Login" and self.wizard_state.get("client") is None:
                self._next_btn.configure(state="disabled")

    # -- Navigation ---------------------------------------------------------

    def go_next(self) -> None:
        step_name = WIZARD_STEPS[self._current_step]
        screen = self._screens[step_name]
        if hasattr(screen, "validate") and not screen.validate():
            return
        if self._current_step < len(WIZARD_STEPS) - 1:
            self._show_screen_at_index(self._current_step + 1)

    def go_back(self) -> None:
        if self._current_step > 0:
            self._show_screen_at_index(self._current_step - 1)

    def go_to_screen(self, name: str) -> None:
        if name in WIZARD_STEPS:
            self._show_screen_at_index(WIZARD_STEPS.index(name))

    def enable_next(self) -> None:
        self._next_btn.configure(state="normal")

    def disable_next(self) -> None:
        self._next_btn.configure(state="disabled")

    def enable_back(self) -> None:
        self._back_btn.configure(state="normal")


def launch_gui() -> None:
    """Create and run the AOL Email Exporter wizard application."""
    app = AOLExporterApp()
    app.mainloop()
