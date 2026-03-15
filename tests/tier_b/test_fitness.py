# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Fitness tests — architectural invariants enforced by CI.

These tests verify structural properties of the codebase, not behavior.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.tier_b

_SRC = Path(__file__).resolve().parents[2] / "src" / "mailpail"
_SCREEN_DIR = _SRC / "ui" / "screens"
_UI_FILES = list((_SRC / "ui").rglob("*.py"))


def _read_py(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestNoHardcodedColors:
    """No raw hex color literals in screen files — everything must come from theme."""

    def _screen_files(self) -> list[Path]:
        return [f for f in _SCREEN_DIR.glob("*.py") if f.name != "__init__.py"]

    def test_no_raw_hex_in_screens(self):
        """Screen files must not contain hardcoded hex color strings."""
        # Pattern: quoted hex color like "#FFFFFF" or "#1E8449"
        hex_pattern = re.compile(r"""["']#[0-9A-Fa-f]{6}["']""")
        violations: list[str] = []

        for path in self._screen_files():
            content = _read_py(path)
            for i, line in enumerate(content.splitlines(), 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Allow _CELEBRATION_COLORS definition (complete.py)
                if "_CELEBRATION_COLORS" in line:
                    continue
                matches = hex_pattern.findall(line)
                if matches:
                    violations.append(f"{path.name}:{i}: {matches}")

        assert not violations, "Hardcoded hex colors found:\n" + "\n".join(violations)

    def test_no_raw_hex_in_app(self):
        """app.py must not contain hardcoded hex color strings."""
        hex_pattern = re.compile(r"""["']#[0-9A-Fa-f]{6}["']""")
        app_path = _SRC / "ui" / "app.py"
        content = _read_py(app_path)
        violations: list[str] = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            matches = hex_pattern.findall(line)
            if matches:
                violations.append(f"app.py:{i}: {matches}")

        assert not violations, "Hardcoded hex colors in app.py:\n" + "\n".join(violations)


class TestNoAOLInUI:
    """No 'AOL' in user-visible strings in screen files."""

    def test_no_aol_string_in_screens(self):
        """Screen files must not contain 'AOL' in string literals."""
        violations: list[str] = []

        for path in _SCREEN_DIR.glob("*.py"):
            if path.name == "__init__.py":
                continue
            content = _read_py(path)
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Look for AOL in string literals (not comments or variable names)
                if re.search(r"""["'].*AOL.*["']""", line):
                    violations.append(f"{path.name}:{i}: {line.strip()}")

        assert not violations, "AOL references in screen files:\n" + "\n".join(violations)

    def test_no_aol_in_strings_module(self):
        """strings.py must not contain 'AOL'."""
        strings_path = _SRC / "ui" / "strings.py"
        content = _read_py(strings_path)
        violations: list[str] = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"""["'].*AOL.*["']""", line):
                violations.append(f"strings.py:{i}: {line.strip()}")

        assert not violations, "AOL references in strings.py:\n" + "\n".join(violations)


class TestNoFadeIn:
    """fade_in animation is removed from all screen files."""

    def test_no_fade_in_imports(self):
        """No screen file imports fade_in."""
        violations: list[str] = []
        for path in _UI_FILES:
            if path.name == "theme.py":
                continue
            content = _read_py(path)
            if "fade_in" in content:
                violations.append(path.name)

        assert not violations, f"fade_in still referenced in: {violations}"
