# AOL Email Exporter

[![CI](https://github.com/heymumford/aol-email-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/heymumford/aol-email-exporter/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

A friendly wizard to download and export your AOL email to PDF, Excel, and CSV.

![Wizard Screenshot](docs/screenshot.png)

## Features

- **GUI wizard interface** -- step-by-step guided export
- **IMAP download** with folder and date-range filters
- **4 export formats** -- gzipped CSV, Excel (single or grouped sheets), PDF
- **Browser session detection** -- reuse existing AOL login cookies
- **Cross-platform** -- Windows and POSIX
- **Windows executable** -- standalone `.exe` releases (no Python required)

## Quick Start

### Install from pip

```bash
pip install aol-email-exporter
aol-email-exporter          # launch GUI wizard
aol-email-exporter --cli    # headless mode
```

### Download Windows executable

Grab the latest `.exe` from [Releases](https://github.com/heymumford/aol-email-exporter/releases) and run it.

## CLI Usage

```bash
# Export all mail to gzipped CSV
aol-email-exporter --cli --email user@aol.com --format csv

# Export specific folder to PDF
aol-email-exporter --cli --email user@aol.com --folder Inbox --format pdf

# Export with date range to Excel (grouped by folder)
aol-email-exporter --cli --email user@aol.com --format excel-sheets \
    --after 2024-01-01 --before 2025-01-01

# Use browser cookies instead of password prompt
aol-email-exporter --cli --email user@aol.com --use-cookies --format csv
```

## AOL Setup

AOL requires an **app password** for third-party IMAP access:

1. Go to [AOL Account Security](https://login.aol.com/account/security/app-passwords)
2. Sign in to your AOL account
3. Click **Generate app password**
4. Select "Other App" and give it a name (e.g., "Email Exporter")
5. Copy the generated password
6. Use this password when prompted by the exporter

> **Note:** Your regular AOL password will not work for IMAP access. You must use an app password.

## Export Formats

| Format | Flag | Description |
|--------|------|-------------|
| CSV | `--format csv` | Gzipped `.csv.gz` file with all messages |
| Excel | `--format excel` | Single-sheet `.xlsx` workbook |
| Excel (grouped) | `--format excel-sheets` | Multi-sheet `.xlsx`, one sheet per folder |
| PDF | `--format pdf` | One PDF per message, bundled in a directory |

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
just install    # set up environment
just test       # run all tests
just lint       # check code style
just format     # fix code style
just all        # format + lint + test
```

### Test tiers

- **Tier A** (`just test-a`) -- must-pass product feature scenarios
- **Tier B** (`just test-b`) -- regression and edge case tests

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) for details.

Copyright (c) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
