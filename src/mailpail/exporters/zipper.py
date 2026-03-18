# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Zip the entire export directory into a single .zip archive."""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


def zip_export(output_dir: Path, zip_name: str | None = None) -> Path:
    """Create a .zip archive of everything in output_dir.

    The zip file is placed alongside (not inside) output_dir.
    Returns the path to the zip file.
    """
    if zip_name is None:
        zip_name = f"{output_dir.name}.zip"

    zip_path = output_dir.parent / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(output_dir.rglob("*")):
            if file_path.is_file():
                arcname = file_path.relative_to(output_dir)
                zf.write(file_path, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    logger.info("Zipped export: %s (%.1f MB)", zip_path, size_mb)
    return zip_path
