# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tier B — Phase 3 feature regression tests.

Batch export, exporter plugin system, progress dots grid fix.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.tier_b


class TestExporterPluginSystem:
    def test_exporter_entry_point_group_defined(self):
        from mailpail.exporters import EXPORTER_ENTRY_POINT_GROUP

        assert EXPORTER_ENTRY_POINT_GROUP == "mailpail.exporters"

    def test_available_formats_returns_all_six(self):
        from mailpail.exporters import available_formats

        fmts = available_formats()
        assert set(fmts) >= {"csv", "excel", "excel-sheets", "pdf", "mbox", "eml"}

    def test_plugin_exporters_dont_crash(self):
        """_load_plugin_exporters returns dict even with no plugins installed."""
        from mailpail.exporters import _load_plugin_exporters

        result = _load_plugin_exporters()
        assert isinstance(result, dict)


class TestBatchCLIFlag:
    def test_batch_flag_exists(self):
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--batch", "accounts.csv"])
        assert args.batch == "accounts.csv"

    def test_batch_flag_default_none(self):
        from mailpail.__main__ import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--username", "u@x.com"])
        assert args.batch is None


class TestProgressDotsGrid:
    """T2 tech debt: progress dots should use grid, not place()."""

    def test_progress_dots_use_grid(self):
        """_build_progress_dots must use grid(), not place(), for centering."""
        import inspect

        from mailpail.ui.app import MailpailApp

        source = inspect.getsource(MailpailApp._build_progress_dots)
        assert ".place(" not in source, "_build_progress_dots still uses place()"
        assert ".grid(" in source, "_build_progress_dots should use grid()"
