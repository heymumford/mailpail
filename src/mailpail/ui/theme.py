# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import platform

_SYSTEM = platform.system()


def _system_font() -> str:
    """Return the platform-native UI font family."""
    if _SYSTEM == "Darwin":
        return ".AppleSystemUIFont"
    if _SYSTEM == "Windows":
        return "Segoe UI Variable"
    return "Noto Sans"


_FONT = _system_font()

# Apple HIG-aligned palette — bright, vibrant, modern on every platform.
COLORS: dict[str, str] = {
    "bg": "#F5F5F7",
    "fg": "#1D1D1F",
    "accent": "#007AFF",
    "accent_hover": "#0056CC",
    "success": "#34C759",
    "success_bg": "#E8F5E9",
    "success_hover": "#1E8449",
    "warning": "#FF9500",
    "error": "#FF3B30",
    "error_hover": "#C0392B",
    "card": "#FFFFFF",
    "subtle": "#636366",  # darkened from #86868B for WCAG AA (4.6:1 on #F5F5F7)
    "subtle_hover": "#6B7585",
    "border": "#D2D2D7",
    "sidebar": "#F0F0F5",
    "hover": "#E8E8ED",
    "button_text": "#FFFFFF",
}

FONTS: dict[str, tuple[str, int]] = {
    "header": (_FONT, 28),
    "subheader": (_FONT, 20),
    "body": (_FONT, 16),
    "label": (_FONT, 14),
    "small": (_FONT, 12),
    "button": (_FONT, 18),
    "icon_large": (_FONT, 72),
    "icon": (_FONT, 48),
    "dot": (_FONT, 14),
    "connector": (_FONT, 10),
}

ICONS: dict[str, str] = {
    "welcome": "\U0001f4e8",
    "login": "\U0001f511",
    "folder": "\U0001f4c1",
    "filter": "\U0001f50d",
    "format": "\U0001f4be",
    "progress": "\u2b07",
    "complete": "\u2705",
    "back": "\u2190",
    "next": "\u2192",
    "error": "\u26a0",
}

WIZARD_STEPS: list[str] = [
    "Welcome",
    "Login",
    "Folders",
    "Filters",
    "Format",
    "Download",
    "Complete",
]

ACCEL_PREFIX: str = "Cmd" if _SYSTEM == "Darwin" else "Ctrl"


# Dark mode palette — activated by customtkinter.set_appearance_mode("dark")
COLORS_DARK: dict[str, str] = {
    "bg": "#1C1C1E",
    "fg": "#F5F5F7",
    "accent": "#0A84FF",
    "accent_hover": "#409CFF",
    "success": "#30D158",
    "success_bg": "#1A3A1F",
    "success_hover": "#28A745",
    "warning": "#FF9F0A",
    "error": "#FF453A",
    "error_hover": "#FF6961",
    "card": "#2C2C2E",
    "subtle": "#98989D",
    "subtle_hover": "#8E8E93",
    "border": "#38383A",
    "sidebar": "#252528",
    "hover": "#3A3A3C",
    "button_text": "#FFFFFF",
}


def get_colors(mode: str = "light") -> dict[str, str]:
    """Return the color palette for the given appearance mode."""
    return COLORS_DARK if mode == "dark" else COLORS
