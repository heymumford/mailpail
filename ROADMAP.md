# Mailpail Product Roadmap

**Last updated:** 2026-03-18
**Version:** 1.0.0
**License:** GPL-3.0-or-later

## North Star

**"Your email, your files, your machine."**

Mailpail is a local-first desktop tool for non-technical users to connect their email accounts, build filters, and export matching messages and attachments to zipped CSV on Windows and POSIX. Not an email client, not a sync tool, not a migration service. One job: get your mail out in a format you control.

**Design test for every feature:** Can Margaret (68, retired teacher, AOL user) complete this without reading documentation or asking for help?

## What Mailpail Is NOT

- Not an email client (no compose, reply, or sync)
- Not a migration tool (no IMAP-to-IMAP transfer)
- Not a search engine (no full-text index)
- Not an archival system (no dedup or long-term retention policy)
- Not a cloud service (everything stays on your machine)

## The DSL Boundary

```
provider + credentials → connection
connection + filters  → message set
message set + format  → export artifact (with attachments)
export artifact + zip → done
```

Every feature must fit this pipeline. If it doesn't, it's out of scope or belongs in a plugin.

## Competitive Landscape

### Open Source Tools (GitHub)

| Tool | Stars | Lang | What It Does | Strengths | Weaknesses | Relationship |
|------|------:|------|-------------|-----------|------------|-------------|
| **imap-backup** | 1,700 | Ruby | IMAP backup + migrate, Maildir/mbox | Incremental, OAuth2, Thunderbird export, active | CLI-only, no CSV/Excel/PDF, no filtering | Compete (different audience) |
| **imapsync** | 3,400+ | Perl | IMAP-to-IMAP transfer | De facto migration standard, battle-tested | IMAP-only (no local formats), $60 license | Different niche |
| **Gmvault** | 3,600 | Python | Gmail backup | Large community, Gmail-specific features | Dormant, Gmail-only, CLI-only, Python 2 era | Dead competitor |
| **MailVault** | 61 | Rust/React | Desktop email backup → local .eml | Native desktop (Tauri), OAuth2, dark mode | macOS/Linux only (v2.2), no export formats, no filtering | Direct competitor |
| **imapbox** | 237 | Python | IMAP → HTML/PDF/JSON + attachments | Multiple formats, Elasticsearch, dedup | CLI-only, no filtering, requires wkhtmltopdf | Potential library |
| **attachment-downloader** | 95 | Python | Download IMAP attachments | Regex filtering, date range, Jinja2 templates | CLI-only, attachments only (no message body) | Potential include |
| **imap_tools** | 813 | Python | Python IMAP library | Rich query builder, AND/OR/NOT, typed API | Library (not end-user tool) | **Already a dependency** |
| **email2pdf** | 70 | Python | Email → PDF conversion | Attachment extraction, getmail integration | Archived/deprecated (2021), no GUI | Dead, concept absorbed |
| **NoPriv** | ~200 | Python | IMAP → browsable HTML archive | Human-readable output, GPLv3 | Python 2, unmaintained | Dead |
| **gwbackupy** | ~100 | Python | Google Workspace backup | Service account support, Gmvault alternative | Google-only, CLI-only | Different niche |

### Commercial Tools

| Tool | Platform | Price | Strengths | Weaknesses |
|------|----------|-------|-----------|------------|
| **MailStore Home** | Windows | Free | Full-text search, PST/EML/MBOX, mature | Windows-only, closed source, no multi-provider export |
| **Aid4Mail** | Windows | $50+ | eDiscovery, many formats, chain of custody | Windows-only, commercial, enterprise pricing |
| **SysTools IMAP Backup** | Win/Mac | $49+ | 30+ formats, date filter, batch accounts | Commercial, overwhelming UI, upsell-heavy |
| **Aryson IMAP Backup** | Windows | $49+ | CSV/PDF/PST/EML export, simple GUI | Windows-only, commercial |
| **Mail Backup X** | Win/Mac | $30+ | Multiple account backup, scheduled | Commercial, email client not exporter |
| **Moth Software** | Windows | $30+ | Professional archiving, format conversion | Windows-only, commercial |

### Mailpail's Empty Niche

No existing tool combines ALL of these:

| Capability | imap-backup | MailVault | MailStore | imapsync | mbsync | **Mailpail** |
|------------|:-----------:|:---------:|:---------:|:--------:|:------:|:------------:|
| Cross-platform (Win + POSIX) | Y | - | - | Y | Y | **Y** |
| GUI wizard for non-technical users | - | Y | Y | - | - | **Y** |
| CLI for scripting | Y | - | - | Y | Y | **Y** |
| Multi-provider (AOL, Gmail, Outlook, Yahoo, custom) | Y | Y | Y | Y | Y | **Y** |
| Filtered export (date, folder, sender, subject) | - | - | Y | - | - | **Y** |
| CSV/Excel export | - | - | - | - | - | **Y** |
| PDF export | - | - | - | - | - | **Y** |
| Attachment download | Y | Y | Y | - | Y | **Y** |
| Plugin extensible | - | - | - | - | - | **Y** |
| Open source | Y | Y | - | - | Y | **Y** |
| Zipped output | - | - | - | - | - | **Y** |

**Strategic position:** The only open-source, cross-platform, GUI + CLI email exporter with filtered export to human-readable formats AND plugin extensibility. Every competitor is either CLI-only, single-platform, commercial, or lacks format conversion.

## Personas

| Name | Age | Context | Primary Need | Technical Level |
|------|-----|---------|-------------|-----------------|
| **Margaret** | 68 | Retired teacher, AOL mail since 2001, 22 years of emails | "I want to save my emails before I forget my password" | Minimal — opens apps, follows wizards |
| **Ray** | 54 | Small business owner, Yahoo + Gmail | "I need monthly backups of my business correspondence" | Basic — comfortable with file explorer |
| **Derek** | 35 | IT consultant, manages client migrations | "I need bulk export across providers with scriptable CLI" | Advanced — uses terminal daily |
| **Sandra** | 42 | Paralegal, needs email evidence for cases | "I need filtered exports with timestamps and integrity hashes" | Moderate — follows procedures precisely |

## Must-Have Features (Industry Standard)

Based on competitive analysis and user expectations for email export tools:

### Table Stakes (every competitor has these)
1. **IMAP connection with TLS** — secure connection to any IMAP server
2. **Multi-provider support** — Gmail, Outlook, Yahoo, AOL, custom IMAP
3. **App password authentication** — modern providers require it
4. **Folder listing and selection** — user picks which folders to export
5. **Attachment download** — export is incomplete without attachments
6. **Date range filtering** — most requested filter criterion
7. **Progress indication** — users need to know it's working
8. **Error handling with clear messages** — "wrong password" not stack traces

### Differentiators (Mailpail's edge)
9. **Wizard-guided UI** — step-by-step, no configuration files
10. **Filtered export to CSV** — structured data, not raw email files
11. **Zipped output** — single artifact, portable, space-efficient
12. **Plugin system** — third-party providers and exporters via entry points
13. **Cross-platform executable** — .exe for Windows, native for POSIX

### Advanced (eDiscovery / professional use)
14. **SHA-256 hash manifest** — chain of custody for legal use
15. **Export log with timestamps** — structured audit artifact
16. **Incremental export** — don't re-download on subsequent runs
17. **MBOX/EML standard formats** — interop with other email tools

## Current State (v0.1.0 Alpha)

### Implemented
- GUI wizard: 7 screens (welcome, login, folders, filters, formats, progress, complete)
- CLI mode (`--cli` flag)
- 5 built-in providers (AOL, Gmail, Outlook, Yahoo, custom IMAP)
- Provider plugin system via entry points (`mailpail.providers`)
- 5 exporters: CSV (gzipped), Excel (single/grouped), PDF, EML, MBOX
- Client-side filtering (date, folder)
- BaseScreen skeleton for consistent UI
- Theme system (WCAG AA compliant)
- Centralized strings (strings.py)
- Cookie detection (opt-in button)

### Broken / Tech Debt

| # | Item | Severity | Notes |
|---|------|----------|-------|
| ~~T0~~ | ~~Test suite doesn't run~~ | ~~Critical~~ | Fixed: hatch build config + `python -m pytest` invocation |
| T1 | Screens don't inherit BaseScreen | Medium | Skeleton exists, no screen uses it |
| T2 | `place()` in progress dots | Low | Should use grid |
| T3 | UI integration test hardcodes widget traversal | Medium | BaseScreen migration will break paths |
| T4 | ExportConfig.pdf_title defaults to "Email Export" | Low | Should come from strings.py |
| T5 | No CI workflow for PyPI publish | Medium | release.yml builds .exe but no PyPI |
| T6 | browser_cookie3 not in optional extras properly | Low | Triggers Keychain popups |
| T7 | client.py display_name hardcodes "AOL Mail" | Low | Should come from ProviderDescriptor |
| T8 | No `type: ignore` audit | Low | Scattered comments need review |
| T9 | test_ui_integration.py not in CI | Medium | Needs headless runner |

## Product Roadmap

### Phase 0: Foundation Fix (COMPLETE)

**Delivered:** v0.2.0

| # | Item | Status |
|---|------|--------|
| 0.1 | Fix test suite import error (hatch build config + pytest invocation) | Done |
| 0.2 | All screens inherit BaseScreen | Deferred (screens already functional, refactor is cosmetic) |
| 0.3 | Progress screen reassurance text | Done (already rendered) |
| 0.4 | Wire LoginScreen to AuthFlow.form_fields() | Done (provider dropdown + dynamic form) |
| 0.5 | Fix client.py display_name | Done (uses `IMAP ({server})`) |
| 0.6 | browser_cookie3 → optional extras | Done (in `[cookies]` extras group) |

### Phase 1: Attachment & Export Completeness (COMPLETE)

**Delivered:** v0.2.0. 140 tests green.

| # | Item | Status |
|---|------|--------|
| 1.1 | Attachment download in all 6 formats (CSV, Excel, PDF, EML, MBOX + saved to disk) | Done |
| 1.2 | Zipped output (entire export dir → single .zip alongside) | Done |
| 1.3 | Subject/sender/keyword filter | Done (already in FilterScreen + CLI `--sender`/`--subject`) |
| 1.4 | Export manifest (JSON with SHA-256 hashes, file sizes, record counts) | Done |
| 1.5 | Default output dir to Desktop (GUI already uses `~/Desktop/Mailpail_Export`) | Done |
| 1.6 | EML + MBOX format options in GUI format screen | Done |
| 1.7 | Attachment filenames column in CSV and Excel exports | Done |
| 1.8 | Attachment filenames listed in PDF per-email pages | Done |

### Phase 2: Polish & Publish (COMPLETE)

**Delivered:** v0.3.0. 202 tests green.

| # | Item | Status |
|---|------|--------|
| 2.1 | PyPI publish workflow (trusted publishing via `pypa/gh-action-pypi-publish`) | Done |
| 2.2 | Windows .exe + macOS app in GitHub Releases (already in release.yml) | Done |
| 2.3 | SHA-256 hash manifest | Done (Phase 1, `manifest.py`) |
| 2.4 | Export log with timestamps (`export_log.json` — filters, folders, errors, warnings) | Done |
| 2.5 | Incremental export (`--incremental` CLI flag, `.mailpail_exported` UID tracking) | Done |
| 2.6 | Folder structure preservation | Done (records carry folder attribute; Excel-sheets groups by folder) |
| 2.7 | Dark mode palette (WCAG AA verified, `COLORS_DARK`, `get_colors()`) | Done |
| 2.8 | CI: PyPI publish workflow in release.yml | Done |

### Phase 3: Professional & Legal Use (COMPLETE)

**Delivered:** v0.4.0. 216 tests green.

| # | Item | Status |
|---|------|--------|
| 3.1 | Batch export (`--batch accounts.csv` — multiple accounts, one run) | Done |
| 3.2 | PST export | Deferred (requires pypst dependency; not on critical path) |
| 3.3 | OAuth PKCE browser flow | Blocked (AOL/Yahoo don't grant new OAuth2 registrations) |
| 3.4 | Scheduled/recurring backup | Deferred (daemon mode is scope creep for MVP) |
| 3.5 | Multi-account in single GUI session | Deferred (batch CLI covers Derek's use case) |
| 3.6 | Exporter plugin entry point group (`mailpail.exporters`) | Done |

**Also fixed:**
- T2: Progress dots use grid instead of place()
- `available_formats()` helper for plugin-aware format discovery

### Phase 4: Community & Growth (COMPLETE)

**Delivered:** v1.0.0. 217 tests green.

| # | Item | Status |
|---|------|--------|
| 4.1 | 1.0.0 stability release | Done |
| 4.2 | Plugin cookbook (README documents both entry point groups) | Done |
| 4.3 | Localization framework (strings.py centralized, i18n-ready) | Ready |
| 4.4 | Post-export search | Deferred (post-1.0) |
| 4.5 | Homebrew formula | Deferred (post-1.0, needs PyPI publish first) |
| 4.6 | Show HN launch | Ready (README, roadmap, all features documented) |

## Partner / Include Opportunities

| Project | GitHub | Integration | Value Exchange |
|---------|--------|------------|----------------|
| **imap_tools** | 813 stars | Already a dependency | We consume their query builder; they get a GUI frontend user base |
| **imapbox** | 237 stars | Study their HTML/PDF pipeline | Their Elasticsearch integration could inspire post-export search |
| **attachment-downloader** | 95 stars | Study their Jinja2 filename templates | Template-based output naming is a good UX pattern |
| **imap-backup** | 1.7k stars | Interop via MBOX format | They backup, we export. Complementary workflows. |

## Plugin Roadmap

| Plugin | Entry Point | AuthFlow | Priority | Notes |
|--------|------------|----------|----------|-------|
| `mailpail-gmail-oauth` | `gmail-oauth` | OAuthPKCEFlow | P1 (Phase 3) | Gmail deprecating app passwords |
| `mailpail-graph` | `outlook-graph` | MSALFlow | P2 | Outlook via Microsoft Graph API |
| `mailpail-mbox` | n/a (exporter) | n/a | Done | MBOX export (built-in as of v0.1.0) |
| `mailpail-eml` | n/a (exporter) | n/a | Done | EML per-message export (built-in as of v0.1.0) |
| `mailpail-pst` | n/a (exporter) | n/a | P1 (Phase 3) | PST export via pypst |

## Success Metrics

| Phase | Metric | Target |
|-------|--------|--------|
| 0 | Test suite | 100% pass, green CI |
| 1 | Margaret test | Complete export in <5 wizard steps, no documentation needed |
| 2 | PyPI installs | First 100 installs within 2 weeks of publish |
| 2 | GitHub stars | 50 within first month |
| 3 | Professional adoption | 1 paralegal or IT consultant using it for real work |
| 4 | Community plugins | 3+ third-party plugins published |

## Update Policy

- This file is the canonical product roadmap for Mailpail.
- `BACKLOG.md` is the detailed backlog with persona rationale (retained for reference).
- `task_plan.md` is the execution tracker for current sprint work.
- Update this file first when product priorities change.
