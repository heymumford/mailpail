# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import os
import platform
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger("mailpail")

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(funcName)s:%(lineno)d %(message)s"

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5


def _default_log_path() -> Path:
    """Return the platform-appropriate default log file path."""
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(base) / "mailpail" / "logs" / "exporter.log"
    return Path.home() / ".local" / "log" / "mailpail" / "exporter.log"


def _add_file_handler(log_file: str | None) -> None:
    """Attach a RotatingFileHandler, creating parent directories as needed."""
    path = Path(log_file) if log_file else _default_log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(str(path), maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.debug("File logging enabled: %s", path)
    except PermissionError:
        logger.warning("Permission denied writing log to %s — continuing without file handler", path)


def _add_syslog_handler() -> None:
    """Attach a SysLogHandler on POSIX systems."""
    if platform.system() == "Windows":
        try:
            from logging.handlers import NTEventLogHandler  # type: ignore[attr-defined]

            handler = NTEventLogHandler("Mailpail")
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(handler)
            logger.debug("Windows Event Log handler enabled")
        except Exception:  # noqa: BLE001
            logger.warning("NTEventLogHandler unavailable — syslog not supported on this Windows system")
        return

    from logging.handlers import SysLogHandler

    system = platform.system()
    if system == "Darwin":
        address = "/var/run/syslog"
    else:
        address = "/dev/log"

    if not os.path.exists(address):
        logger.warning("Syslog socket %s not found — skipping syslog handler", address)
        return

    try:
        handler = SysLogHandler(address=address)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.debug("Syslog handler enabled via %s", address)
    except Exception:  # noqa: BLE001
        logger.warning("Failed to connect to syslog at %s", address)


def setup_logging(level: str = "INFO", log_file: str | None = None, syslog: bool = False) -> None:
    """Configure logging for the application.

    Args:
        level: Log level name (DEBUG, INFO, WARNING, ERROR).
        log_file: Explicit log file path. Pass empty string to use platform default.
                  Pass None to skip file logging entirely.
        syslog: Enable syslog (POSIX) or Windows Event Log.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Remove any previously-attached handlers (idempotent reconfiguration).
    logger.handlers.clear()

    # Console handler — always enabled, writes to stderr.
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console)

    # File handler — when explicitly requested.
    if log_file is not None:
        _add_file_handler(log_file if log_file else None)

    # Syslog / Event Log handler.
    if syslog:
        _add_syslog_handler()
