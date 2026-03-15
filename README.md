# Mailpail

[![CI](https://github.com/heymumford/mailpail/actions/workflows/ci.yml/badge.svg)](https://github.com/heymumford/mailpail/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

Carry your mail away in a pail. A friendly wizard to download and export your email to PDF, Excel, and CSV.

![Wizard Screenshot](docs/screenshot.png)

## Features

- **GUI wizard interface** -- step-by-step guided export
- **IMAP download** with folder and date-range filters
- **4 export formats** -- gzipped CSV, Excel (single or grouped sheets), PDF
- **Browser session detection** -- reuse existing login cookies
- **Multiple providers** -- AOL, Gmail, Outlook, Yahoo, custom IMAP
- **Cross-platform** -- Windows and POSIX
- **Windows executable** -- standalone `.exe` releases (no Python required)

## Quick Start

### Install from pip

```bash
pip install mailpail
mailpail          # launch GUI wizard
mailpail --cli    # headless mode
```

### Download Windows executable

Grab the latest `.exe` from [Releases](https://github.com/heymumford/mailpail/releases) and run it.

## CLI Usage

```bash
# Export all mail to gzipped CSV
mailpail --cli --username user@aol.com --format csv

# Export specific folder to PDF
mailpail --cli --username user@aol.com --folder Inbox --format pdf

# Export with date range to Excel (grouped by folder)
mailpail --cli --username user@aol.com --format excel-sheets \
    --date-from 2024-01-01 --date-to 2025-01-01

# Use browser cookies instead of password prompt
mailpail --cli --username user@aol.com --use-cookies --format csv
```

## App Password Setup

Most email providers require an **app password** for third-party IMAP access:

**AOL:**
1. Go to [AOL Account Security](https://login.aol.com/account/security/app-passwords)
2. Generate an app password

**Gmail:**
1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Generate an app password (requires 2FA enabled)

> **Note:** Your regular password will not work for IMAP access. You must use an app password.

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
