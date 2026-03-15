# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from aol_email_exporter.logging_config import setup_logging


pytestmark = pytest.mark.tier_a

LOGGER_NAME = "aol_email_exporter"


class TestLogging:
    """Logging configuration tests."""

    def _get_logger(self) -> logging.Logger:
        return logging.getLogger(LOGGER_NAME)

    def test_setup_logging_default(self):
        setup_logging()
        logger = self._get_logger()
        # At least one handler (console) is present
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "StreamHandler" in handler_types
        assert logger.level == logging.INFO

    def test_setup_logging_with_file(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        setup_logging(log_file=log_file)
        logger = self._get_logger()
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "RotatingFileHandler" in handler_types
        assert Path(log_file).parent.exists()

    def test_setup_logging_debug_level(self):
        setup_logging(level="DEBUG")
        logger = self._get_logger()
        assert logger.level == logging.DEBUG

    def test_log_file_directory_created(self, tmp_path):
        nested = tmp_path / "sub" / "dir" / "app.log"
        setup_logging(log_file=str(nested))
        assert nested.parent.exists()

    def test_setup_logging_idempotent(self):
        """Calling setup_logging twice clears old handlers."""
        setup_logging(level="WARNING")
        setup_logging(level="ERROR")
        logger = self._get_logger()
        assert logger.level == logging.ERROR
        # Should have exactly the console handler, not duplicates
        stream_handlers = [h for h in logger.handlers if type(h).__name__ == "StreamHandler"]
        assert len(stream_handlers) == 1
