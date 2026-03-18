# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier B — Phase 2 feature regression tests.

Dark mode palette, CLI incremental flag, release workflow, export log
structure.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.tier_b


class TestDarkMode:
    def test_dark_palette_exists(self):
        from mailpail.ui.theme import COLORS_DARK

        assert isinstance(COLORS_DARK, dict)
        assert len(COLORS_DARK) > 0

    def test_dark_palette_has_all_keys(self):
        from mailpail.ui.theme import COLORS, COLORS_DARK

        missing = set(COLORS.keys()) - set(COLORS_DARK.keys())
        assert not missing, f"Dark palette missing keys: {missing}"

    def test_get_colors_light(self):
        from mailpail.ui.theme import COLORS, get_colors

        assert get_colors("light") is COLORS

    def test_get_colors_dark(self):
        from mailpail.ui.theme import COLORS_DARK, get_colors

        assert get_colors("dark") is COLORS_DARK

    def test_dark_bg_is_actually_dark(self):
        from mailpail.ui.theme import COLORS_DARK

        bg = COLORS_DARK["bg"]
        # Parse hex and verify it's dark (luminance < 0.3)
        r = int(bg[1:3], 16) / 255
        g = int(bg[3:5], 16) / 255
        b = int(bg[5:7], 16) / 255
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        assert luminance < 0.3, f"Dark mode bg ({bg}) is not dark enough: luminance={luminance:.2f}"

    def test_dark_fg_is_actually_light(self):
        from mailpail.ui.theme import COLORS_DARK

        fg = COLORS_DARK["fg"]
        r = int(fg[1:3], 16) / 255
        g = int(fg[3:5], 16) / 255
        b = int(fg[5:7], 16) / 255
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        assert luminance > 0.7, f"Dark mode fg ({fg}) is not light enough: luminance={luminance:.2f}"

    def test_dark_contrast_ratio(self):
        """WCAG AA requires 4.5:1 contrast for normal text."""
        from mailpail.ui.theme import COLORS_DARK

        def relative_luminance(hex_color: str) -> float:
            r = int(hex_color[1:3], 16) / 255
            g = int(hex_color[3:5], 16) / 255
            b = int(hex_color[5:7], 16) / 255
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        bg_lum = relative_luminance(COLORS_DARK["bg"])
        fg_lum = relative_luminance(COLORS_DARK["fg"])
        lighter = max(bg_lum, fg_lum)
        darker = min(bg_lum, fg_lum)
        ratio = (lighter + 0.05) / (darker + 0.05)
        assert ratio >= 4.5, f"Dark mode contrast ratio {ratio:.1f} below WCAG AA (4.5:1)"


class TestCLIIncrementalFlag:
    def test_incremental_flag_exists(self):
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com", "--incremental"])
        assert args.incremental is True

    def test_incremental_default_false(self):
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com"])
        assert args.incremental is False


class TestExportLogStructure:
    def test_log_has_timestamp(self, tmp_path):
        import json

        from mailpail.exporters.export_log import write_export_log
        from mailpail.models import ExportResult

        result = ExportResult(format_name="csv", file_path="/tmp/x.csv", record_count=1, success=True)
        path = write_export_log(tmp_path, [result], total_emails=1)
        data = json.loads(path.read_text())
        # ISO 8601 timestamp
        assert "T" in data["timestamp_utc"]
        assert data["timestamp_utc"].endswith("+00:00")

    def test_log_version_matches_package(self, tmp_path):
        import json

        from mailpail import __version__
        from mailpail.exporters.export_log import write_export_log
        from mailpail.models import ExportResult

        result = ExportResult(format_name="csv", file_path="/tmp/x.csv", record_count=0, success=True)
        path = write_export_log(tmp_path, [result], total_emails=0)
        data = json.loads(path.read_text())
        assert data["mailpail_version"] == __version__


class TestReleaseWorkflow:
    """Verify release.yml is structurally sound."""

    def test_release_yml_exists(self):
        from pathlib import Path

        workflow = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release.yml"
        assert workflow.exists()

    def test_release_yml_has_pypi_job(self):
        from pathlib import Path

        workflow = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release.yml"
        content = workflow.read_text()
        assert "publish-pypi" in content
        assert "pypa/gh-action-pypi-publish" in content

    def test_release_yml_has_trusted_publishing(self):
        from pathlib import Path

        workflow = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release.yml"
        content = workflow.read_text()
        assert "id-token: write" in content
