# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import threading
import webbrowser
from typing import TYPE_CHECKING

import customtkinter

from mailpail.providers import DEFAULT_PROVIDER, PROVIDERS, ProviderDescriptor
from mailpail.ui.strings import (
    APP_PASSWORD_DEFAULT,
    APP_PASSWORD_SETUP,
    LOGIN_AUTH_FAILED,
    LOGIN_BOTH_REQUIRED,
    LOGIN_CONNECTED,
    LOGIN_CONNECTING,
    LOGIN_HELP_LINK,
    LOGIN_NETWORK_FAILED,
    LOGIN_SESSION_DETECTED,
    LOGIN_SESSION_FOUND,
    LOGIN_TEST_CONNECTION,
    LOGIN_TITLE,
    LOGIN_UNKNOWN_FAILED,
    LOGIN_USE_SESSION,
    REASSURANCE_READONLY,
)
from mailpail.ui.theme import COLORS, FONTS, ICONS

if TYPE_CHECKING:
    from mailpail.ui.app import MailpailApp


class LoginScreen(customtkinter.CTkFrame):
    """Wizard step 2 — credentials and connection test."""

    def __init__(self, parent: customtkinter.CTkFrame, app: MailpailApp) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self._app = app
        self._client: object | None = None
        self._testing = False
        self._provider_key = DEFAULT_PROVIDER
        self._build()

    def _current_provider(self) -> ProviderDescriptor:
        return PROVIDERS.get(self._provider_key, PROVIDERS[DEFAULT_PROVIDER])

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
            text=LOGIN_TITLE,
            font=(FONTS["header"][0], FONTS["header"][1], "bold"),
            text_color=COLORS["fg"],
        ).pack(side="left")

        # Provider dropdown
        provider_frame = customtkinter.CTkFrame(self, fg_color=COLORS["bg"])
        provider_frame.grid(row=2, column=0, padx=60, pady=(0, 8), sticky="ew")

        customtkinter.CTkLabel(
            provider_frame,
            text="Email Provider:",
            font=FONTS["label"],
            text_color=COLORS["fg"],
        ).pack(side="left", padx=(0, 8))

        provider_names = [PROVIDERS[k].name for k in sorted(PROVIDERS.keys())]
        self._provider_var = customtkinter.StringVar(value=self._current_provider().name)
        self._provider_dropdown = customtkinter.CTkComboBox(
            provider_frame,
            values=provider_names,
            variable=self._provider_var,
            font=FONTS["label"],
            height=36,
            state="readonly",
            command=self._on_provider_changed,
        )
        self._provider_dropdown.pack(side="left", fill="x", expand=True)

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
            text=LOGIN_USE_SESSION,
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
        form_card.grid(row=4, column=0, padx=60, pady=(8, 0), sticky="ew")

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
            text="Password",
            font=FONTS["label"],
            text_color=COLORS["fg"],
            anchor="w",
        ).pack(padx=24, pady=(4, 4), anchor="w")

        self._password_entry = customtkinter.CTkEntry(
            form_card,
            placeholder_text="Password or App Password",
            font=FONTS["body"],
            show="*",
            height=44,
            corner_radius=8,
        )
        self._password_entry.pack(padx=24, pady=(0, 8), fill="x")

        # App password setup instructions (updates per provider)
        self._setup_label = customtkinter.CTkLabel(
            form_card,
            text=APP_PASSWORD_SETUP.get(self._provider_key, APP_PASSWORD_DEFAULT),
            font=FONTS["small"],
            text_color=COLORS["fg"],
            wraplength=500,
            justify="left",
            anchor="w",
        )
        self._setup_label.pack(padx=24, pady=(4, 8), anchor="w", fill="x")

        # Help link
        self._help_link = customtkinter.CTkLabel(
            form_card,
            text=LOGIN_HELP_LINK,
            font=FONTS["small"],
            text_color=COLORS["accent"],
            cursor="hand2",
        )
        self._help_link.pack(padx=24, pady=(0, 8), anchor="w")
        self._help_link.bind("<Button-1>", lambda _e: self._open_help())

        # Reassurance text
        customtkinter.CTkLabel(
            form_card,
            text=REASSURANCE_READONLY,
            font=FONTS["small"],
            text_color=COLORS["subtle"],
            wraplength=500,
        ).pack(padx=24, pady=(0, 12), anchor="w")

        # Button row
        btn_row = customtkinter.CTkFrame(form_card, fg_color=COLORS["card"])
        btn_row.pack(padx=24, pady=(0, 8), fill="x")

        self._test_btn = customtkinter.CTkButton(
            btn_row,
            text=LOGIN_TEST_CONNECTION,
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["button_text"],
            corner_radius=8,
            height=44,
            width=200,
            command=self._test_connection,
        )
        self._test_btn.pack(side="left", padx=(0, 8))

        self._cookie_btn = customtkinter.CTkButton(
            btn_row,
            text="Check Browser Session",
            font=FONTS["label"],
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["subtle"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            height=44,
            width=200,
            command=self._check_browser_session,
        )
        self._cookie_btn.pack(side="left")

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
        """Called when this screen becomes visible. No auto cookie detection."""
        self._session_card.grid_forget()
        self._detected_session = None

    def _on_provider_changed(self, choice: str) -> None:
        """Update internal state and setup instructions when provider changes."""
        for key, desc in PROVIDERS.items():
            if desc.name == choice:
                self._provider_key = key
                self._app.wizard_state["provider_key"] = key
                # Update setup instructions for the selected provider
                setup_text = APP_PASSWORD_SETUP.get(key, APP_PASSWORD_DEFAULT)
                self._setup_label.configure(text=setup_text)
                break

    def _open_help(self) -> None:
        provider = self._current_provider()
        url = provider.help_url
        if url:
            webbrowser.open(url)

    def _check_browser_session(self) -> None:
        """Explicitly check for browser session (opt-in, no auto-detect)."""
        self._cookie_btn.configure(state="disabled", text="Checking...")
        thread = threading.Thread(target=self._detect_session_bg, daemon=True)
        thread.start()

    def _detect_session_bg(self) -> None:
        """Check for an existing browser session (background thread)."""
        try:
            from mailpail.cookie_auth import detect_browser_session

            session = detect_browser_session()
            if session is not None:
                self._app.run_on_main(self._show_session_card, session)
            else:
                self._app.run_on_main(self._no_session_found)
        except Exception:
            self._app.run_on_main(self._no_session_found)

    def _show_session_card(self, session: object) -> None:
        """Display the detected session card (main thread)."""
        self._detected_session = session
        self._cookie_btn.configure(state="normal", text="Check Browser Session")
        self._session_card.grid(row=3, column=0, padx=60, pady=(0, 12), sticky="ew")
        self._session_label.configure(
            text=LOGIN_SESSION_FOUND.format(
                browser=session.browser,
                username=session.username,  # type: ignore[union-attr]
            )
        )

    def _no_session_found(self) -> None:
        self._cookie_btn.configure(state="normal", text="Check Browser Session")
        self._status_label.configure(text="No browser session found.", text_color=COLORS["subtle"])

    def _use_detected_session(self) -> None:
        """Auto-fill email from detected browser session."""
        if hasattr(self, "_detected_session") and self._detected_session is not None:
            self._email_entry.delete(0, "end")
            self._email_entry.insert(0, self._detected_session.username)
            self._email_entry.focus_set()
            self._status_label.configure(text=LOGIN_SESSION_DETECTED, text_color=COLORS["accent"])

    def _test_connection(self) -> None:
        """Run connection test in a background thread."""
        if self._testing:
            return

        email_addr = self._email_entry.get().strip()
        password = self._password_entry.get().strip()

        if not email_addr or not password:
            self._status_label.configure(
                text=f"{ICONS['error']} {LOGIN_BOTH_REQUIRED}",
                text_color=COLORS["error"],
            )
            return

        self._testing = True
        self._test_btn.configure(state="disabled", text=LOGIN_CONNECTING)
        self._status_label.configure(text=LOGIN_CONNECTING, text_color=COLORS["subtle"])

        thread = threading.Thread(target=self._run_connection_test, args=(email_addr, password), daemon=True)
        thread.start()

    def _run_connection_test(self, email_addr: str, password: str) -> None:
        """Execute connection test off the main thread using provider's adapter_factory."""
        try:
            from mailpail.auth import Credential

            provider = self._current_provider()
            credential = Credential(
                provider_key=provider.key,
                data={"username": email_addr, "password": password},
            )
            client = provider.adapter_factory(credential)
            client.connect()
            self._client = client
            self._app.run_on_main(self._on_connection_success, email_addr, password)
        except Exception as exc:
            self._app.run_on_main(self._on_connection_failure, str(exc))

    def _on_connection_success(self, email_addr: str, password: str) -> None:
        """Update UI after successful connection (runs on main thread)."""
        self._testing = False
        self._test_btn.configure(state="normal", text=LOGIN_TEST_CONNECTION)
        self._status_label.configure(text=LOGIN_CONNECTED, text_color=COLORS["success"])
        self._app.wizard_state["username"] = email_addr
        self._app.wizard_state["password"] = password
        self._app.wizard_state["client"] = self._client
        self._app.wizard_state["provider_key"] = self._provider_key
        self._app.enable_next()

    def _on_connection_failure(self, error_msg: str) -> None:
        """Update UI after failed connection with helpful guidance."""
        self._testing = False
        self._test_btn.configure(state="normal", text=LOGIN_TEST_CONNECTION)

        # Categorize the error for user-friendly display
        error_lower = error_msg.lower()
        if "authentication" in error_lower or "credentials" in error_lower or "login" in error_lower:
            display_msg = LOGIN_AUTH_FAILED
        elif "refused" in error_lower or "timeout" in error_lower or "reach" in error_lower:
            display_msg = LOGIN_NETWORK_FAILED
        else:
            display_msg = LOGIN_UNKNOWN_FAILED

        self._status_label.configure(
            text=f"{ICONS['error']} {display_msg}",
            text_color=COLORS["error"],
        )
        self._app.disable_next()

    def validate(self) -> bool:
        """Return True if the user has a valid connection."""
        return self._client is not None and self._app.wizard_state.get("client") is not None
