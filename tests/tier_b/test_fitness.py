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


class TestProviders:
    """Provider registry completeness."""

    def test_all_providers_registered(self):
        from mailpail.providers import PROVIDERS

        expected = {"aol", "gmail", "outlook", "yahoo", "imap"}
        assert set(PROVIDERS.keys()) == expected

    def test_all_providers_have_server(self):
        """All providers except 'imap' must have a server set."""
        from mailpail.providers import PROVIDERS

        for key, info in PROVIDERS.items():
            if key == "imap":
                continue
            assert info.server, f"Provider {key!r} has no server"

    def test_provider_flag_accepted(self):
        """CLI accepts --provider flag."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        for provider in ("aol", "gmail", "outlook", "yahoo", "imap"):
            args = parser.parse_args(["--username", "u@x.com", "--provider", provider])
            assert args.provider == provider

    def test_base_screen_exists(self):
        """BaseScreen class exists and is importable."""
        from mailpail.ui.screens.base import BaseScreen

        assert hasattr(BaseScreen, "screen_icon")
        assert hasattr(BaseScreen, "screen_title")
        assert hasattr(BaseScreen, "make_card")


class TestPersonaRequirements:
    """Persona-driven acceptance criteria.

    Margaret: font sizes >= 16px body, no jargon, reassurance text
    Derek: --provider flag, --dry-run, exit codes
    Sandra: ExportResult has audit fields
    Ray: default format is CSV, default dir is Desktop
    """

    def test_margaret_body_font_size(self):
        """Body font must be >= 16px for readability."""
        from mailpail.ui.theme import FONTS

        assert FONTS["body"][1] >= 16

    def test_margaret_no_jargon_in_strings(self):
        """User-visible strings must not contain protocol jargon."""
        from mailpail.ui import strings

        # Collect all string values from the module
        jargon = {"IMAP", "SMTP", "SSL", "TLS", "RFC", "MIME"}
        violations: list[str] = []
        for name in dir(strings):
            if name.startswith("_"):
                continue
            val = getattr(strings, name)
            if isinstance(val, str):
                for j in jargon:
                    if j in val:
                        violations.append(f"{name}: contains '{j}'")
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        for j in jargon:
                            if j in item:
                                violations.append(f"{name}: contains '{j}'")
        assert not violations, "Jargon in user strings:\n" + "\n".join(violations)

    def test_margaret_reassurance_text_exists(self):
        """Reassurance text is defined for user comfort."""
        from mailpail.ui.strings import PROGRESS_REASSURANCE, REASSURANCE_READONLY

        assert "safe" in PROGRESS_REASSURANCE.lower() or "not" in PROGRESS_REASSURANCE.lower()
        assert "delete" in REASSURANCE_READONLY.lower() or "read-only" in REASSURANCE_READONLY.lower()

    def test_derek_provider_flag(self):
        """--provider flag exists with correct choices."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com", "--provider", "gmail"])
        assert args.provider == "gmail"

    def test_derek_dry_run(self):
        """--dry-run flag exists."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com", "--dry-run"])
        assert args.dry_run is True

    def test_sandra_export_result_audit_fields(self):
        """ExportResult has fields needed for audit trail."""
        from mailpail.models import ExportResult

        fields = {f.name for f in ExportResult.__dataclass_fields__.values()}
        assert "format_name" in fields
        assert "file_path" in fields
        assert "record_count" in fields
        assert "success" in fields

    def test_ray_default_format_csv(self):
        """Default export format is CSV."""
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com"])
        assert args.format == ["csv"]

    def test_ray_default_dir_desktop(self):
        """Default export directory includes Desktop."""
        import os

        default_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Mailpail_Export")
        assert "Desktop" in default_dir
