# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Centralized user-visible text for all Mailpail screens.

Every string the user can see lives here. Screen modules import
from this file instead of hardcoding text. This makes i18n,
persona validation, and grep-based auditing straightforward.
"""

from __future__ import annotations

# -- App-level ---------------------------------------------------------------

APP_NAME = "Mailpail"
APP_SUBTITLE = "Carry your mail away in a pail"

# -- Welcome screen ----------------------------------------------------------

WELCOME_TITLE = "Mailpail"
WELCOME_SUBTITLE = "Save your emails safely to your computer"
WELCOME_FEATURES = [
    "Download your emails",
    "Filter by date, sender, or subject",
    "Save as PDF, Excel, or CSV",
]
WELCOME_GET_STARTED = "Get Started"

# -- Login screen ------------------------------------------------------------

LOGIN_TITLE = "Sign In"
LOGIN_EMAIL_LABEL = "Email Address"
LOGIN_EMAIL_PLACEHOLDER = "your.email@example.com"
LOGIN_PASSWORD_LABEL = "App Password"
LOGIN_PASSWORD_PLACEHOLDER = "App Password"
LOGIN_HELP_LINK = "Need an app password? Check your provider's settings \u2197"
LOGIN_TEST_CONNECTION = "Test Connection"
LOGIN_CONNECTING = "Connecting..."
LOGIN_CONNECTED = "\u2705 Connected successfully!"
LOGIN_SESSION_FOUND = "\u2705 We found your session in {browser}! Email: {username}"
LOGIN_USE_SESSION = "Use This Account"
LOGIN_SESSION_DETECTED = "Session detected \u2014 enter your app password to connect."
LOGIN_BOTH_REQUIRED = "Please enter both email and password."

# -- Folders screen ----------------------------------------------------------

FOLDERS_TITLE = "Choose Folders"
FOLDERS_SUBTITLE = "Select which folders to download"
FOLDERS_LOADING = "Loading folders..."
FOLDERS_NONE = "No folders found."
FOLDERS_NO_CONNECTION = "No connection. Go back and sign in."
FOLDERS_SELECT_ALL = "Select All"
FOLDERS_DESELECT_ALL = "Deselect All"

# -- Filters screen ----------------------------------------------------------

FILTERS_TITLE = "Filter Emails (Optional)"
FILTERS_SUBTITLE = "Leave blank to download everything"
FILTERS_SKIP = "Skip Filters"

# -- Format screen -----------------------------------------------------------

FORMAT_TITLE = "Choose Export Formats"
FORMAT_BROWSE = "Browse"
FORMAT_SAVE_TO = "Save to:"

# -- Progress screen ---------------------------------------------------------

PROGRESS_TITLE = "Downloading Emails"
PROGRESS_PREPARING = "Preparing..."
PROGRESS_CANCEL = "Cancel"
PROGRESS_CANCELLING = "Cancelling..."
PROGRESS_CANCELLED = "Download cancelled."
PROGRESS_EXPORTING = "Exporting..."
PROGRESS_COMPLETE = "Export complete!"
PROGRESS_REASSURANCE = "Your emails are safe. Nothing is being deleted from your account."

# -- Complete screen ---------------------------------------------------------

COMPLETE_TITLE = "Export Complete!"
COMPLETE_OPEN_FOLDER = "Open Output Folder"
COMPLETE_EXPORT_AGAIN = "Export Again"
COMPLETE_EXIT = "Exit"

# -- Menu bar ----------------------------------------------------------------

MENU_NEW_EXPORT = "New Export\u2026"
MENU_OPEN_FOLDER = "Open Export Folder"
MENU_APP_PASSWORD_HELP = "App Password Help"
MENU_GITHUB = "GitHub Repository"
MENU_TEST_CONNECTION = "Test Connection\u2026"
MENU_LIST_FOLDERS = "List Folders"
MENU_DISCONNECT = "Disconnect"
MENU_RESET = "Reset Wizard"

# -- Shared ------------------------------------------------------------------

REASSURANCE_READONLY = "This connects read-only. We will not modify or delete any emails."
