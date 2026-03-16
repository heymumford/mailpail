# Mailpail

[![CI](https://github.com/heymumford/mailpail/actions/workflows/ci.yml/badge.svg)](https://github.com/heymumford/mailpail/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

Carry your mail away in a pail. A friendly wizard to download and export your email to PDF, Excel, and CSV.

## Features

- **GUI wizard interface** -- step-by-step guided export
- **Multiple providers** -- AOL, Gmail, Outlook, Yahoo, custom IMAP
- **4 export formats** -- gzipped CSV, Excel (single or grouped sheets), PDF
- **Plugin system** -- third-party providers via `pip install mailpail-*`
- **Cross-platform** -- Windows and POSIX
- **Windows executable** -- standalone `.exe` releases (no Python required)

## Quick Start

```bash
pip install mailpail
mailpail              # launch GUI wizard
mailpail --cli        # headless mode
```

Or grab the latest `.exe` from [Releases](https://github.com/heymumford/mailpail/releases).

## CLI Usage

```bash
# Export all mail to gzipped CSV (AOL, default provider)
mailpail --cli --username user@aol.com --format csv

# Use Gmail instead
mailpail --cli --username user@gmail.com --provider gmail --format csv

# Outlook
mailpail --cli --username user@outlook.com --provider outlook --format excel

# Export specific folder to PDF
mailpail --cli --username user@aol.com --folder Inbox --format pdf

# Export with date range to Excel (grouped by folder)
mailpail --cli --username user@aol.com --format excel-sheets \
    --date-from 2024-01-01 --date-to 2025-01-01

# Dry run -- show count without exporting
mailpail --cli --username user@aol.com --dry-run

# Custom IMAP server
mailpail --cli --username user@example.com --provider imap \
    --server mail.example.com --port 993 --format csv
```

### Provider flag

| Provider | Flag | Server |
|----------|------|--------|
| AOL (default) | `--provider aol` | export.imap.aol.com |
| Gmail | `--provider gmail` | imap.gmail.com |
| Outlook / Hotmail | `--provider outlook` | outlook.office365.com |
| Yahoo | `--provider yahoo` | imap.mail.yahoo.com |
| Custom | `--provider imap --server HOST` | (you specify) |

## App Password Setup

Most email providers require an **app password** for third-party IMAP access:

| Provider | Setup link |
|----------|-----------|
| AOL | [AOL Account Security](https://login.aol.com/account/security/app-passwords) |
| Gmail | [Google App Passwords](https://myaccount.google.com/apppasswords) (requires 2FA) |
| Outlook | [Microsoft App Passwords](https://support.microsoft.com/en-us/account-billing/manage-app-passwords-for-two-step-verification) |
| Yahoo | [Yahoo App Passwords](https://help.yahoo.com/kb/generate-manage-third-party-passwords-sln15241.html) |

Your regular password will not work for IMAP access. You must use an app password.

## Export Formats

| Format | Flag | Description |
|--------|------|-------------|
| CSV | `--format csv` | Gzipped `.csv.gz` file with all messages |
| Excel | `--format excel` | Single-sheet `.xlsx` workbook |
| Excel (grouped) | `--format excel-sheets` | Multi-sheet `.xlsx`, one sheet per folder |
| PDF | `--format pdf` | One PDF per message, bundled in a directory |

## Plugin System

Mailpail supports third-party provider plugins via Python entry points. Install a plugin and its provider appears in the GUI dropdown and CLI `--provider` flag automatically.

### Writing a plugin

Create a Python package with an entry point in `pyproject.toml`:

```toml
[project.entry-points."mailpail.providers"]
my-provider = "my_plugin.descriptor:DESCRIPTOR"
```

The entry point must resolve to a `ProviderDescriptor` instance. See `src/mailpail/providers.py` for the contract and `src/mailpail/auth.py` for the `AuthFlow` Protocol.

A plugin needs to provide:
- A `ProviderDescriptor` with `auth_flow`, `capabilities`, and `adapter_factory`
- An `AuthFlow` implementation (form-based or OAuth browser redirect)
- An adapter class satisfying the `EmailProvider` Protocol

The core handles discovery, GUI rendering, and credential storage. Your plugin handles authentication and email retrieval.

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
just install    # set up environment
just test       # run all tests (100 tests)
just lint       # check code style
just format     # fix code style
just all        # format + lint + test
```

### Test tiers

- **Tier A** (`just test-a`) -- must-pass product feature scenarios
- **Tier B** (`just test-b`) -- regression, edge cases, fitness tests, persona verification

### Architecture

```
src/mailpail/
    __main__.py        # CLI + GUI entry point
    auth.py            # AuthFlow Protocol, Credential, Capability flags
    client.py          # IMAPClient (built-in adapter)
    credentials.py     # Credential storage (env, memory, file)
    providers.py       # ProviderDescriptor, provider registry
    plugin.py          # Entry-point-based plugin discovery
    models.py          # EmailRecord, FilterParams, ExportConfig
    filters.py         # Client-side email filtering
    exporters/         # CSV, Excel, PDF exporters
    ui/                # customtkinter GUI wizard
        screens/       # 7 wizard screens + BaseScreen skeleton
        theme.py       # Colors, fonts, icons
        strings.py     # All user-visible text
```

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) for details.

Copyright (c) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
