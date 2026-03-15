# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import platform
import tkinter as tk

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
    "warning": "#FF9500",
    "error": "#FF3B30",
    "card": "#FFFFFF",
    "subtle": "#86868B",
    "border": "#D2D2D7",
    "sidebar": "#F0F0F5",
    "hover": "#E8E8ED",
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


# ---------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------


def fade_in(widget: tk.Widget, steps: int = 10, delay_ms: int = 30) -> None:
    """Animate widget appearance by stepping opacity from 0.0 to 1.0."""
    toplevel = widget.winfo_toplevel()
    if widget is toplevel:
        _fade_toplevel(widget, steps, delay_ms)
    else:
        _fade_widget(widget, steps, delay_ms)


def _fade_toplevel(window: tk.Widget, steps: int, delay_ms: int) -> None:
    window.attributes("-alpha", 0.0)  # type: ignore[union-attr]

    def _step(i: int) -> None:
        if i > steps:
            return
        try:
            window.attributes("-alpha", i / steps)  # type: ignore[union-attr]
        except tk.TclError:
            return
        window.after(delay_ms, _step, i + 1)

    _step(1)


def _fade_widget(widget: tk.Widget, steps: int, delay_ms: int) -> None:
    widget.after(0, lambda: _reveal_children(widget, steps, delay_ms, 0))


def _reveal_children(widget: tk.Widget, steps: int, delay_ms: int, current: int) -> None:
    if current > steps:
        return
    ratio = current / steps if steps > 0 else 1.0
    blended = _interpolate_color(COLORS["bg"], COLORS["fg"], ratio)
    try:
        _apply_text_color(widget, blended)
    except tk.TclError:
        return
    widget.after(delay_ms, _reveal_children, widget, steps, delay_ms, current + 1)


def _interpolate_color(start_hex: str, end_hex: str, ratio: float) -> str:
    s = _hex_to_rgb(start_hex)
    e = _hex_to_rgb(end_hex)
    r = int(s[0] + (e[0] - s[0]) * ratio)
    g = int(s[1] + (e[1] - s[1]) * ratio)
    b = int(s[2] + (e[2] - s[2]) * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _apply_text_color(widget: tk.Widget, color: str) -> None:
    if hasattr(widget, "configure"):
        try:
            widget.configure(text_color=color)
        except (tk.TclError, ValueError):
            pass
    for child in widget.winfo_children():
        _apply_text_color(child, color)
