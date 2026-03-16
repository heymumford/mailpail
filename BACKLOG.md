# Mailpail Product Backlog

## What Mailpail Is

A context-bound DSL for filtered email export. Local-first desktop app (GUI wizard + CLI) that downloads messages and attachments from IMAP providers and writes them to standard formats on disk. Not an email client, not a sync tool, not a migration service. One job: get your mail out.

## Competitive Landscape

### Direct Competitors (local desktop email export)

| Tool | Platform | License | Strengths | Weaknesses |
|------|----------|---------|-----------|------------|
| **MailVault** | POSIX (Swift) | OSS (GPL) | Native macOS, SQLite archive, free, HN traction | macOS-only, no CLI, no filtering, no export formats |
| **MailStore Home** | Windows | Freeware | Mature, full-text search, PST/EML/MBOX | Windows-only, no CLI, closed source, no multi-provider |
| **Handy Backup** | Windows | Commercial | Scheduled backups, IMAP plugin | Windows-only, $39+, overkill for email-only |
| **imapsync** | POSIX (Perl) | Custom/$60 | De facto IMAP migration standard, incremental | IMAP-to-IMAP only (no local format export), not free anymore |
| **isync/mbsync** | POSIX (C) | ISC | Fast, Maildir output, well-maintained | Developer-oriented, no GUI, Maildir only |
| **OfflineIMAP** | POSIX (Python) | GPL | Python, two-way sync, Maildir | Two-way sync is dangerous for backup, partially maintained |
| **getmail** | POSIX (Python) | GPL | One-way, safe, Python | Manual folder listing, no GUI, raw Maildir/mbox only |
| **GYB** | POSIX (Python) | Apache | Gmail-specific, Google API | Gmail-only, complex OAuth setup |
| **Aid4Mail** | Windows | Commercial ($50+) | eDiscovery features, many formats | Windows-only, commercial, enterprise-priced |

### Mailpail's Differentiation

Mailpail occupies an empty niche: **cross-platform, open-source, GUI + CLI, multi-provider, filtered export to human-readable formats (PDF, Excel, CSV)**. No existing tool combines all of these.

| Capability | MailVault | MailStore | imapsync | mbsync | getmail | **Mailpail** |
|------------|----------|-----------|----------|--------|---------|-------------|
| Cross-platform | - | - | Y | Y | Y | **Y** |
| GUI wizard | Y | Y | - | - | - | **Y** |
| CLI scriptable | - | - | Y | Y | Y | **Y** |
| Multi-provider | Y | Y | Y | Y | Y | **Y** |
| PDF/Excel/CSV export | - | - | - | - | - | **Y** |
| Filtered export | - | Y | - | - | - | **Y** |
| Plugin extensible | - | - | - | - | - | **Y** |
| Open source | Y | - | - | Y | Y | **Y** |
| Attachment download | Y | Y | - | Y | Y | **planned** |

## Product Backlog

### P0: Must-Have (next release)

| # | Item | Persona | Rationale |
|---|------|---------|-----------|
| 1 | **Attachment download** | All | Every competitor does this. Without attachments, the export is incomplete. Must save attachments alongside messages in all formats. |
| 2 | **MBOX/EML export formats** | Derek, Sandra | Standard email archive formats. Derek needs them for migration tooling. Sandra needs EML for litigation support tools. CSV/Excel/PDF serve Margaret and Ray but not technical users. |
| 3 | **Wire LoginScreen to AuthFlow.form_fields()** | All | The plugin architecture exists but LoginScreen still hardcodes the email+password form. Provider dropdown should drive the form dynamically. |
| 4 | **Cookie detection opt-in** | All | Currently auto-detects on show, triggers Keychain popups. Change to explicit "Check Browser Session" button. |
| 5 | **All screens inherit BaseScreen** | Margaret | BaseScreen skeleton exists but screens don't use it yet. Consistent layout, 44px buttons, uniform card pattern. |
| 6 | **Progress screen reassurance text** | Margaret, Ray | strings.py has PROGRESS_REASSURANCE and REASSURANCE_READONLY defined but they're not rendered in the progress screen. |

### P1: Should-Have (v0.2)

| # | Item | Persona | Rationale |
|---|------|---------|-----------|
| 7 | **SHA-256 hash manifest** | Sandra | ExportResult needs a hash field. Each exported file gets a checksum. Manifest file lists all hashes. Chain-of-custody documentation for legal use. |
| 8 | **Export log with timestamps** | Sandra, Derek | Machine-parseable log of what was exported, when, how many messages, any errors. Goes beyond Python logging into a structured audit artifact. |
| 9 | **Provider dropdown in login screen** | All | ProviderInfo registry has 5 providers. Login screen needs a CTkComboBox at top that updates form labels, help URL, and server info per provider. |
| 10 | **Folder structure preservation** | Derek | Export should mirror IMAP folder hierarchy in the output directory. Currently flattens to a single file. |
| 11 | **Incremental export (don't re-download)** | Ray, Derek | Track what's been exported (by UID). Skip already-exported messages on subsequent runs. Essential for Ray's recurring backup use case. |
| 12 | **--output-dir default to Desktop** | Ray, Margaret | Default in CLI is `./export`. GUI defaults to `~/Desktop/Mailpail_Export`. CLI should match GUI default when run without `--output-dir`. |

### P2: Nice-to-Have (v0.3+)

| # | Item | Persona | Rationale |
|---|------|---------|-----------|
| 13 | **Scheduled/recurring backup** | Ray | Daemon or cron-based mode: `mailpail --schedule weekly`. Lowest-friction retention for small business. |
| 14 | **Multi-account in single GUI session** | Ray | Add accounts, export all at once. Ray has Yahoo + Gmail. |
| 15 | **Search within exported archives** | Ray | Post-export full-text search. Could be a separate tool (`mailpail search`) or index file. |
| 16 | **OAuth PKCE browser flow** | Derek | Gmail is deprecating app passwords. Need a real OAuth flow. This is the first plugin candidate (mailpail-gmail-oauth). |
| 17 | **PST export** | Sandra, Derek | Outlook PST is the lingua franca of eDiscovery. Requires `pypst` or similar. |
| 18 | **Dark mode** | All | customtkinter supports it. theme.py needs a dark palette. |
| 19 | **PyPI publish** | All | `pip install mailpail` should work. Needs pyproject.toml classifiers, build workflow, TestPyPI dry run. |
| 20 | **Windows .exe in Releases** | Margaret, Ray | release.yml already builds it. Needs a tag + release cut. |

## Tech Debt

| # | Item | Severity | Notes |
|---|------|----------|-------|
| T1 | **Screens don't inherit BaseScreen** | Medium | BaseScreen exists but no screen uses it. Sprint 2 plan was to migrate all 7 screens. |
| T2 | **place() still used in progress dots** | Low | `_build_progress_dots()` uses `place()` for centering. Should use grid. |
| T3 | **UI integration test hardcodes widget traversal** | Medium | `test_ui_integration.py` uses `_find_widgets` by class name. BaseScreen migration will break traversal paths. |
| T4 | **ExportConfig.pdf_title still defaults to "Email Export"** | Low | Should come from strings.py. |
| T5 | **No CI workflow for PyPI publish** | Medium | release.yml builds executables but doesn't publish to PyPI. |
| T6 | **browser_cookie3 dependency** | Low | Triggers Keychain access popups on POSIX. Should be optional (extras group), not required. Move to `[project.optional-dependencies]`. |
| T7 | **client.py display_name returns hardcoded "AOL Mail"** | Low | IMAPClient.display_name should come from the ProviderDescriptor, not be hardcoded. |
| T8 | **No type: ignore audit** | Low | Several `# type: ignore` comments scattered. Need a pass to verify each is justified. |
| T9 | **test_ui_integration.py not in CI** | Medium | Excluded via `addopts = "--ignore=tests/test_ui_integration.py"`. Needs headless xvfb runner or separate CI job. |

## Architecture Observations

### What Mailpail Is NOT

- Not an email client (no compose, no reply, no sync)
- Not a migration tool (no IMAP-to-IMAP transfer)
- Not a search engine (no full-text index of exported mail)
- Not an archival system (no deduplication, no compression beyond gzip CSV)

### The DSL Boundary

Mailpail's domain language is:

```
provider + credentials → connection
connection + filters → message set
message set + format → export artifact
export artifact + location → done
```

Every feature should fit this pipeline. If it doesn't, it's out of scope or belongs in a plugin.

### Plugin Opportunities (concrete)

| Plugin | Entry point key | AuthFlow | What it adds |
|--------|----------------|----------|-------------|
| `mailpail-gmail-oauth` | `gmail-oauth` | OAuthPKCEFlow | Gmail via OAuth2, replaces app-password flow |
| `mailpail-graph` | `outlook-graph` | MSALFlow | Outlook via Microsoft Graph API |
| `mailpail-mbox` | n/a (exporter) | n/a | MBOX export format (exporter plugin, separate entry point group) |
| `mailpail-eml` | n/a (exporter) | n/a | EML per-message export |
| `mailpail-pst` | n/a (exporter) | n/a | PST export via pypst |

Note: exporter plugins need a second entry point group (`mailpail.exporters`) following the same pattern as `mailpail.providers`.
