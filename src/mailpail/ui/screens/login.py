# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import threading
import webbrowser
from typing import TYPE_CHECKING

import customtkinter

from mailpail.client import IMAPClient
from mailpail.ui.theme import COLORS, FONTS, ICONS

if TYPE_CHECKING:
    from mailpail.ui.app import MailpailApp


class LoginScreen(customtkinter.CTkFrame):
    """Wizard step 2 — credentials and connection test."""

    def __init__(self, parent: customtkinter.CTkFrame, app: MailpailApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._client: IMAPClient | None = None
        self._testing = False
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(10, weight=2)

        # Header
        header_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        header_frame.grid(row=1, column=0, pady=(0, 8))

        customtkinter.CTkLabel(
            header_frame,
            text=ICONS["login"],
            font=FONTS["icon"],
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 12))

        customtkinter.CTkLabel(
            header_frame,
            text="Sign In",
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["fg"],
        ).pack(side="left")

        # Session detection card (hidden initially)
        self._session_card = customtkinter.CTkFrame(
            self,
            fg_color=COLORS["success_bg"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["success"],
            height=80,
        )
        self._session_label = customtkinter.CTkLabel(
            self._session_card,
            text="",
            font=FONTS["body"],
            text_color=COLORS["success"],
            wraplength=500,
        )
        self._session_label.pack(padx=20, pady=8)

        self._use_session_btn = customtkinter.CTkButton(
            self._session_card,
            text="Use This Account",
            font=FONTS["label"],
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            text_color=COLORS["button_text"],
            corner_radius=8,
            height=36,
            command=self._use_detected_session,
        )
        self._use_session_btn.pack(padx=20, pady=(0, 12))

        # Form card
        form_card = customtkinter.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        form_card.grid(row=3, column=0, padx=60, pady=(8, 0), sticky="ew")

        # Email field
        customtkinter.CTkLabel(
            form_card,
            text="Email Address",
            font=FONTS["label"],
            text_color=COLORS["fg"],
            anchor="w",
        ).pack(padx=24, pady=(20, 4), anchor="w")

        self._email_entry = customtkinter.CTkEntry(
            form_card,
            placeholder_text="your.email@example.com",
            font=FONTS["body"],
            height=44,
            corner_radius=8,
        )
        self._email_entry.pack(padx=24, pady=(0, 12), fill="x")

        # Password field
        customtkinter.CTkLabel(
            form_card,
            text="App Password",
            font=FONTS["label"],
            text_color=COLORS["fg"],
            anchor="w",
        ).pack(padx=24, pady=(4, 4), anchor="w")

        self._password_entry = customtkinter.CTkEntry(
            form_card,
            placeholder_text="App Password",
            font=FONTS["body"],
            show="*",
            height=44,
            corner_radius=8,
        )
        self._password_entry.pack(padx=24, pady=(0, 8), fill="x")

        # Help link
        help_link = customtkinter.CTkLabel(
            form_card,
            text="Need an app password? Check your provider's settings \u2197",
            font=FONTS["small"],
            text_color=COLORS["accent"],
            cursor="hand2",
        )
        help_link.pack(padx=24, pady=(0, 16), anchor="w")
        help_link.bind(
            "<Button-1>",
            lambda _e: webbrowser.open("https://login.aol.com/account/security/app-passwords"),
        )

        # Test Connection button
        self._test_btn = customtkinter.CTkButton(
            form_card,
            text="Test Connection",
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["button_text"],
            corner_radius=8,
            height=44,
            width=200,
            command=self._test_connection,
        )
        self._test_btn.pack(padx=24, pady=(4, 8))

        # Status label
        self._status_label = customtkinter.CTkLabel(
            form_card,
            text="",
            font=FONTS["label"],
            text_color=COLORS["subtle"],
        )
        self._status_label.pack(padx=24, pady=(0, 20))

        self._form_card = form_card

    def on_show(self) -> None:
        """Called when this screen becomes visible."""
        # Run cookie detection in background — it probes multiple browsers
        # and can take several seconds.
        self._session_card.grid_forget()
        self._detected_session = None
        thread = threading.Thread(target=self._detect_session_bg, daemon=True)
        thread.start()

    def _detect_session_bg(self) -> None:
        """Check for an existing browser session (background thread)."""
        try:
            from mailpail.cookie_auth import detect_browser_session

            session = detect_browser_session()
            if session is not None:
                self._app.run_on_main(self._show_session_card, session)
        except Exception:
            pass

    def _show_session_card(self, session: object) -> None:
        """Display the detected session card (main thread)."""
        self._detected_session = session
        self._session_card.grid(row=2, column=0, padx=60, pady=(0, 12), sticky="ew")
        self._session_label.configure(
            text=f"\u2705 We found your session in {session.browser}! Email: {session.username}"  # type: ignore[union-attr]
        )

    def _use_detected_session(self) -> None:
        """Auto-fill email from detected browser session."""
        if hasattr(self, "_detected_session") and self._detected_session is not None:
            self._email_entry.delete(0, "end")
            self._email_entry.insert(0, self._detected_session.username)
            self._email_entry.focus_set()
            self._status_label.configure(
                text="Session detected — enter your app password to connect.",
                text_color=COLORS["accent"],
            )

    def _test_connection(self) -> None:
        """Run connection test in a background thread."""
        if self._testing:
            return

        email = self._email_entry.get().strip()
        password = self._password_entry.get().strip()

        if not email or not password:
            self._status_label.configure(
                text=f"{ICONS['error']} Please enter both email and password.",
                text_color=COLORS["error"],
            )
            return

        self._testing = True
        self._test_btn.configure(state="disabled", text="Connecting...")
        self._status_label.configure(text="Connecting...", text_color=COLORS["subtle"])

        thread = threading.Thread(target=self._run_connection_test, args=(email, password), daemon=True)
        thread.start()

    def _run_connection_test(self, email: str, password: str) -> None:
        """Execute connection test off the main thread."""
        try:
            client = IMAPClient(username=email, password=password)
            client.connect()
            self._client = client
            self._app.run_on_main(self._on_connection_success, email, password)
        except Exception as exc:
            self._app.run_on_main(self._on_connection_failure, str(exc))

    def _on_connection_success(self, email: str, password: str) -> None:
        """Update UI after successful connection (runs on main thread)."""
        self._testing = False
        self._test_btn.configure(state="normal", text="Test Connection")
        self._status_label.configure(
            text="\u2705 Connected successfully!",
            text_color=COLORS["success"],
        )
        # Store credentials and client in wizard state
        self._app.wizard_state["username"] = email
        self._app.wizard_state["password"] = password
        self._app.wizard_state["client"] = self._client
        self._app.enable_next()

    def _on_connection_failure(self, error_msg: str) -> None:
        """Update UI after failed connection (runs on main thread)."""
        self._testing = False
        self._test_btn.configure(state="normal", text="Test Connection")
        # Truncate long error messages for display
        display_msg = error_msg if len(error_msg) < 200 else error_msg[:200] + "..."
        self._status_label.configure(
            text=f"{ICONS['error']} {display_msg}",
            text_color=COLORS["error"],
        )
        self._app.disable_next()

    def validate(self) -> bool:
        """Return True if the user has a valid connection."""
        return self._client is not None and self._app.wizard_state.get("client") is not None
