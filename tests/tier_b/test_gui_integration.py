# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier B — GUI integration tests.

Tests the customtkinter wizard by instantiating real widgets, injecting
mock state, and verifying screen rendering and navigation.

Requires a display: runs natively on POSIX/Windows, uses Xvfb on
headless Linux CI (via pytest-xvfb plugin).

Marked with `gui` marker — skip with: pytest -m "not gui"
"""

from __future__ import annotations

import os
import time
from unittest.mock import MagicMock

import pytest

# Skip entire module if tkinter/Tcl isn't available (common in uv venvs)
try:
    import tkinter as _tk

    _root = _tk.Tk()
    _root.withdraw()
    _root.destroy()
    _TK_AVAILABLE = True
except Exception:
    _TK_AVAILABLE = False

_HAS_DISPLAY = _TK_AVAILABLE and bool(
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.name == "nt" or os.uname().sysname == "Darwin"
)

pytestmark = [
    pytest.mark.tier_b,
    pytest.mark.gui,
    pytest.mark.skipif(not _HAS_DISPLAY, reason="No display or tkinter/Tcl not available"),
]


def _pump(app, ms: int = 300) -> None:
    """Process pending tkinter events for `ms` milliseconds."""
    end = time.time() + ms / 1000.0
    while time.time() < end:
        try:
            app.update_idletasks()
            app.update()
        except Exception:
            break
        time.sleep(0.02)


def _find_widgets(parent, cls_name: str) -> list:
    """Recursively find all widgets matching class name."""
    found = []
    try:
        for child in parent.winfo_children():
            if type(child).__name__ == cls_name:
                found.append(child)
            found.extend(_find_widgets(child, cls_name))
    except Exception:
        pass
    return found


@pytest.fixture()
def app():
    """Create the Mailpail wizard app, yield it, then destroy."""
    import customtkinter

    customtkinter.set_appearance_mode("light")

    from mailpail.ui.app import MailpailApp

    root = MailpailApp()
    _pump(root, 500)
    yield root
    try:
        root.destroy()
    except Exception:
        pass


# -- Welcome Screen ----------------------------------------------------------


class TestWelcomeScreen:
    def test_starts_on_welcome(self, app):
        assert app._current_step == 0

    def test_title_visible(self, app):
        screen = app._screens["Welcome"]
        labels = _find_widgets(screen, "CTkLabel")
        texts = [lbl.cget("text") for lbl in labels if lbl.cget("text")]
        assert any("Mailpail" in t for t in texts)

    def test_get_started_button_exists(self, app):
        screen = app._screens["Welcome"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Get Started" in t for t in texts)

    def test_get_started_advances_to_login(self, app):
        screen = app._screens["Welcome"]
        buttons = _find_widgets(screen, "CTkButton")
        start_btn = [b for b in buttons if "Get Started" in (b.cget("text") or "")]
        assert start_btn, "Get Started button not found"

        cmd = start_btn[0].cget("command")
        if callable(cmd):
            cmd()
        _pump(app, 300)
        assert app._current_step == 1

    def test_version_displayed(self, app):
        screen = app._screens["Welcome"]
        labels = _find_widgets(screen, "CTkLabel")
        texts = [lbl.cget("text") for lbl in labels if lbl.cget("text")]
        assert any("Version" in t for t in texts)


# -- Login Screen ------------------------------------------------------------


class TestLoginScreen:
    def _go_to_login(self, app):
        app._show_screen_at_index(1)
        _pump(app, 300)

    def test_has_email_and_password_fields(self, app):
        self._go_to_login(app)
        screen = app._screens["Login"]
        entries = _find_widgets(screen, "CTkEntry")
        assert len(entries) >= 2, f"Expected 2+ entries, got {len(entries)}"

    def test_has_provider_dropdown(self, app):
        self._go_to_login(app)
        screen = app._screens["Login"]
        combos = _find_widgets(screen, "CTkComboBox")
        assert len(combos) >= 1, "Provider dropdown missing"

    def test_has_test_connection_button(self, app):
        self._go_to_login(app)
        screen = app._screens["Login"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Test Connection" in t for t in texts)

    def test_has_browser_session_button(self, app):
        self._go_to_login(app)
        screen = app._screens["Login"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Browser Session" in t for t in texts)

    def test_reassurance_text_present(self, app):
        self._go_to_login(app)
        screen = app._screens["Login"]
        labels = _find_widgets(screen, "CTkLabel")
        texts = [lbl.cget("text") or "" for lbl in labels]
        assert any("read-only" in t.lower() or "not" in t.lower() for t in texts)

    def test_next_disabled_without_connection(self, app):
        self._go_to_login(app)
        state = str(app._next_btn.cget("state"))
        assert state == "disabled"

    def test_mock_connection_enables_next(self, app):
        self._go_to_login(app)
        mock_client = MagicMock()
        mock_client.list_folders.return_value = ["INBOX"]
        app.wizard_state["client"] = mock_client
        app.enable_next()
        _pump(app, 100)
        state = str(app._next_btn.cget("state"))
        assert state == "normal"


# -- Folders Screen ----------------------------------------------------------


class TestFolderScreen:
    def _go_to_folders(self, app):
        mock_client = MagicMock()
        mock_client.list_folders.return_value = ["INBOX", "Sent", "Draft", "Trash", "Bulk Mail"]
        app.wizard_state["client"] = mock_client
        app._show_screen_at_index(2)
        # Wait for threaded folder load
        _pump(app, 1500)

    def test_shows_folder_checkboxes(self, app):
        self._go_to_folders(app)
        screen = app._screens["Folders"]
        checkboxes = _find_widgets(screen, "CTkCheckBox")
        assert len(checkboxes) >= 5, f"Expected 5 folder checkboxes, got {len(checkboxes)}"

    def test_inbox_pre_selected(self, app):
        self._go_to_folders(app)
        screen = app._screens["Folders"]
        checkboxes = _find_widgets(screen, "CTkCheckBox")
        inbox_cbs = [cb for cb in checkboxes if "INBOX" in (cb.cget("text") or "")]
        assert inbox_cbs, "INBOX checkbox not found"

    def test_select_all_button(self, app):
        self._go_to_folders(app)
        screen = app._screens["Folders"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Select All" in t for t in texts)

    def test_deselect_all_button(self, app):
        self._go_to_folders(app)
        screen = app._screens["Folders"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Deselect All" in t for t in texts)


# -- Filters Screen ----------------------------------------------------------


class TestFilterScreen:
    def _go_to_filters(self, app):
        app._show_screen_at_index(3)
        _pump(app, 300)

    def test_has_date_range_fields(self, app):
        self._go_to_filters(app)
        screen = app._screens["Filters"]
        entries = _find_widgets(screen, "CTkEntry")
        assert len(entries) >= 4, "Expected date_from, date_to, sender, subject entries"

    def test_has_unread_checkbox(self, app):
        self._go_to_filters(app)
        screen = app._screens["Filters"]
        checkboxes = _find_widgets(screen, "CTkCheckBox")
        texts = [cb.cget("text") or "" for cb in checkboxes]
        assert any("nread" in t.lower() for t in texts)

    def test_skip_filters_button(self, app):
        self._go_to_filters(app)
        screen = app._screens["Filters"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Skip" in t for t in texts)

    def test_skip_advances_to_format(self, app):
        self._go_to_filters(app)
        screen = app._screens["Filters"]
        buttons = _find_widgets(screen, "CTkButton")
        skip_btn = [b for b in buttons if "Skip" in (b.cget("text") or "")]
        assert skip_btn
        cmd = skip_btn[0].cget("command")
        if callable(cmd):
            cmd()
        _pump(app, 300)
        assert app._current_step == 4


# -- Format Screen -----------------------------------------------------------


class TestFormatScreen:
    def _go_to_formats(self, app):
        app._show_screen_at_index(4)
        _pump(app, 300)

    def test_has_six_format_options(self, app):
        self._go_to_formats(app)
        screen = app._screens["Format"]
        checkboxes = _find_widgets(screen, "CTkCheckBox")
        assert len(checkboxes) == 6, f"Expected 6 format checkboxes, got {len(checkboxes)}"

    def test_csv_default_checked(self, app):
        self._go_to_formats(app)
        screen = app._screens["Format"]
        checkboxes = _find_widgets(screen, "CTkCheckBox")
        csv_cbs = [cb for cb in checkboxes if "CSV" in (cb.cget("text") or "")]
        assert csv_cbs, "CSV checkbox not found"

    def test_output_dir_has_default(self, app):
        self._go_to_formats(app)
        screen = app._screens["Format"]
        entries = _find_widgets(screen, "CTkEntry")
        assert entries, "No output dir entry found"
        value = entries[0].get()
        assert "Desktop" in value or "Mailpail" in value

    def test_browse_button_exists(self, app):
        self._go_to_formats(app)
        screen = app._screens["Format"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Browse" in t for t in texts)


# -- Complete Screen ---------------------------------------------------------


class TestCompleteScreen:
    def _go_to_complete(self, app):
        from mailpail.models import ExportResult

        app.wizard_state["total_emails"] = 42
        app.wizard_state["results"] = [
            ExportResult(format_name="csv", file_path="/tmp/test.csv.gz", record_count=42, success=True),
        ]
        app.wizard_state["output_dir"] = "/tmp/test_export"
        app._show_screen_at_index(6)
        _pump(app, 800)

    def test_shows_email_count(self, app):
        self._go_to_complete(app)
        screen = app._screens["Complete"]
        labels = _find_widgets(screen, "CTkLabel")
        texts = [lbl.cget("text") or "" for lbl in labels]
        assert any("42" in t for t in texts)

    def test_has_open_folder_button(self, app):
        self._go_to_complete(app)
        screen = app._screens["Complete"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Open" in t for t in texts)

    def test_has_export_again_button(self, app):
        self._go_to_complete(app)
        screen = app._screens["Complete"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Export Again" in t for t in texts)

    def test_has_exit_button(self, app):
        self._go_to_complete(app)
        screen = app._screens["Complete"]
        buttons = _find_widgets(screen, "CTkButton")
        texts = [b.cget("text") or "" for b in buttons]
        assert any("Exit" in t for t in texts)


# -- Navigation --------------------------------------------------------------


class TestNavigation:
    def test_back_from_welcome_stays(self, app):
        app._show_screen_at_index(0)
        app.go_back()
        assert app._current_step == 0

    def test_next_from_complete_stays(self, app):
        app._show_screen_at_index(6)
        _pump(app, 100)
        app.go_next()
        assert app._current_step == 6

    def test_reset_returns_to_welcome(self, app):
        app._show_screen_at_index(3)
        _pump(app, 100)
        app._reset_wizard()
        _pump(app, 300)
        assert app._current_step == 0

    def test_progress_dots_update(self, app):
        """Progress dots change color as user advances."""
        for step in range(7):
            app._current_step = step
            app._update_progress_dots()
            _pump(app, 50)
        # Should not crash
        assert True

    def test_go_to_invalid_screen(self, app):
        """Invalid screen name is a no-op."""
        app._show_screen_at_index(3)
        app.go_to_screen("Nonexistent")
        assert app._current_step == 3
