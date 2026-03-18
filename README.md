# Mailpail

[![CI](https://github.com/heymumford/mailpail/actions/workflows/ci.yml/badge.svg)](https://github.com/heymumford/mailpail/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

Your email, your files, your machine. A friendly wizard to download and export your email to CSV, Excel, PDF, MBOX, and EML — with attachments.

## Features

- **GUI wizard** -- step-by-step guided export for non-technical users
- **CLI mode** -- scriptable headless export with full filter support
- **6 export formats** -- gzipped CSV, Excel (single or grouped), PDF, MBOX, EML
- **Attachment download** -- saves all attachments alongside exports
- **Filtered export** -- by date range, sender, subject, folder, unread status
- **5 built-in providers** -- AOL, Gmail, Outlook, Yahoo, custom IMAP
- **Batch export** -- process multiple accounts from a CSV credential file
- **Incremental export** -- skip already-exported emails on subsequent runs
- **Audit trail** -- SHA-256 manifest, timestamped export log, zip archive
- **Plugin system** -- third-party providers and exporters via entry points
- **Cross-platform** -- Windows (.exe), POSIX
- **Dark mode** -- WCAG AA compliant dark palette

## Quick Start

```bash
pip install mailpail
mailpail              # launch GUI wizard
mailpail --cli        # headless mode
```

Or grab the latest `.exe` from [Releases](https://github.com/heymumford/mailpail/releases).

## CLI Usage

```bash
# Export AOL inbox to gzipped CSV (default)
mailpail --cli --username user@aol.com --format csv

# Gmail with date range filter
mailpail --cli --username user@gmail.com --provider gmail \
    --date-from 2024-01-01 --date-to 2025-01-01 --format csv

# Filter by sender and subject
mailpail --cli --username user@aol.com \
    --sender "friend@aol.com" --subject "vacation" --format pdf

# Export to multiple formats at once
mailpail --cli --username user@aol.com --format csv excel pdf

# Incremental export (skip already-downloaded emails)
mailpail --cli --username user@aol.com --incremental --format csv

# Batch export from CSV credential file
mailpail --cli --batch accounts.csv --output-dir ./exports

# Dry run (show count without exporting)
mailpail --cli --username user@aol.com --dry-run

# List available IMAP folders
mailpail --cli --username user@aol.com --list-folders

# Custom IMAP server
mailpail --cli --username user@example.com --provider imap \
    --server mail.example.com --port 993 --format csv
```

### Providers

| Provider | Flag | Server |
|----------|------|--------|
| AOL (default) | `--provider aol` | export.imap.aol.com |
| Gmail | `--provider gmail` | imap.gmail.com |
| Outlook / Hotmail | `--provider outlook` | outlook.office365.com |
| Yahoo | `--provider yahoo` | imap.mail.yahoo.com |
| Custom | `--provider imap --server HOST` | (you specify) |

### Export Formats

| Format | Flag | Description |
|--------|------|-------------|
| CSV | `--format csv` | Gzipped `.csv.gz` with attachment filenames column |
| Excel | `--format excel` | Single-sheet `.xlsx` workbook |
| Excel (grouped) | `--format excel-sheets` | Multi-sheet `.xlsx`, one sheet per folder |
| PDF | `--format pdf` | One PDF with all emails, attachment names listed |
| MBOX | `--format mbox` | Standard email archive with embedded attachments |
| EML | `--format eml` | One `.eml` file per email with attachments |

### Batch Export

Create a CSV file with one account per row:

```csv
username,password,provider,folder,format
margaret@aol.com,abcd-efgh-ijkl-mnop,aol,INBOX,csv
derek@gmail.com,wxyz-1234-5678-abcd,gmail,INBOX,excel
```

Only `username` and `password` are required. Other columns default to: provider=aol, folder=INBOX, format=csv.

```bash
mailpail --cli --batch accounts.csv --output-dir ./exports
```

Each account gets its own subdirectory with export files, manifest, and zip.

## App Password Setup

Most providers require an **app password** (not your regular password):

| Provider | Setup link |
|----------|-----------|
| AOL | [AOL Account Security](https://login.aol.com/account/security/app-passwords) |
| Gmail | [Google App Passwords](https://myaccount.google.com/apppasswords) (requires 2FA) |
| Outlook | [Microsoft App Passwords](https://support.microsoft.com/en-us/account-billing/manage-app-passwords-for-two-step-verification) |
| Yahoo | [Yahoo App Passwords](https://help.yahoo.com/kb/generate-manage-third-party-passwords-sln15241.html) |

## Export Output

Every export produces a self-contained directory:

```
Mailpail_Export/
    mail_export.csv.gz          # your emails
    attachments/                # saved attachment files
        1_invoice.pdf
        5_beach.jpg
    manifest.json               # SHA-256 hashes for every file
    export_log.json             # timestamps, filters, results
    .mailpail_exported          # UID tracking for incremental
Mailpail_Export.zip             # single portable archive
```

## Plugin System

Mailpail supports two plugin entry point groups:

### Provider plugins (`mailpail.providers`)

```toml
[project.entry-points."mailpail.providers"]
my-provider = "my_plugin.descriptor:DESCRIPTOR"
```

### Exporter plugins (`mailpail.exporters`)

```toml
[project.entry-points."mailpail.exporters"]
my-format = "my_plugin.exporter:MyExporter"
```

Plugins are discovered automatically. Provider plugins appear in the GUI dropdown and CLI `--provider` flag. Exporter plugins appear in `--format` choices.

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
just install    # set up environment
just test       # run all tests (217 tests)
just lint       # check code style
just format     # fix code style
just all        # format + lint + test
```

### Test tiers

- **Tier A** (`just test-a`) -- must-pass product feature scenarios (AOL pipeline, exports, attachments, manifest, zip, batch, incremental)
- **Tier B** (`just test-b`) -- regression, fitness, persona, dark mode, plugin system, GUI integration

### Architecture

```
src/mailpail/
    __main__.py          # CLI + GUI entry point
    auth.py              # AuthFlow Protocol, Credential, Capability flags
    batch.py             # Batch export from CSV credential files
    client.py            # IMAPClient (built-in IMAP adapter)
    credentials.py       # Credential storage (env, memory, file)
    filters.py           # Client-side email filtering
    models.py            # EmailRecord, FilterParams, ExportConfig
    plugin.py            # Entry-point-based plugin discovery
    providers.py         # ProviderDescriptor, 5 built-in providers
    exporters/
        __init__.py      # Exporter registry + plugin discovery
        attachments.py   # Save attachments to disk
        csv_export.py    # Gzipped CSV with attachment column
        eml_export.py    # Individual .eml files
        excel_export.py  # Single-sheet and grouped Excel
        export_log.py    # Timestamped audit log
        incremental.py   # UID tracking for skip-already-exported
        manifest.py      # SHA-256 hash manifest
        mbox_export.py   # Standard MBOX archive
        pdf_export.py    # PDF document
        zipper.py        # Zip the export directory
    ui/
        app.py           # Main wizard window
        strings.py       # All user-visible text (i18n-ready)
        theme.py         # Light + dark palettes (WCAG AA)
        screens/         # 7 wizard screens + BaseScreen skeleton
```

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) for details.

Copyright (c) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
