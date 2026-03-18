# Mailpail UI Automated Test Plan

**Version:** 1.0.0
**Last verified:** 2026-03-18
**Framework:** customtkinter 5.2+ (wraps tkinter/Tcl)

## Strategy

### Why not Playwright/Selenium?

Playwright and Selenium drive **browser engines** (Chromium, WebKit, Firefox). Mailpail is a **native desktop app** built on tkinter/Tcl. There is no browser, no DOM, no CDP protocol. Playwright cannot see or interact with tkinter widgets.

### What works

tkinter exposes a complete programmatic API for widget interaction:

| Operation | Method | Notes |
|-----------|--------|-------|
| Click button | `button.invoke()` | Calls the `command` callback directly |
| Fill text entry | `entry.delete(0, "end"); entry.insert(0, value)` | Standard tkinter |
| Check checkbox | `checkbox.select()` | CTkCheckBox method |
| Uncheck checkbox | `checkbox.deselect()` | CTkCheckBox method |
| Read widget text | `widget.cget("text")` | Works on labels, buttons |
| Read entry value | `entry.get()` | Returns current text |
| Read checkbox state | `checkbox.get()` | Returns 0 or 1 |
| Find child widgets | `parent.winfo_children()` (recursive) | All CTk widgets |
| Check visibility | `widget.winfo_viewable()` | True if rendered |
| Process events | `app.update_idletasks(); app.update()` | Pump the event loop |
| Navigate screens | `app._show_screen_at_index(n)` | Direct screen control |

### Three-tier test architecture

```
┌─────────────────────────────────────────────────────┐
│  Tier 1: Logic Tests (no display)                   │
│  Models, filters, exporters, auth, providers        │
│  Run: `just test` (CI + local, all platforms)       │
│  Count: 217 tests                                   │
├─────────────────────────────────────────────────────┤
│  Tier 2: Widget Integration Tests (display needed)  │
│  Screen rendering, widget presence, navigation,     │
│  form validation, button commands                   │
│  Run: `just test-gui` (needs tkinter in uv venv)    │
│  Count: 49 tests                                    │
├─────────────────────────────────────────────────────┤
│  Tier 3: Visual Smoke Tests (headful, local only)   │
│  Full wizard walkthrough with screenshots           │
│  Run: `python tests/test_ui_integration.py`         │
│  Count: 9 tests                                     │
└─────────────────────────────────────────────────────┘
```

### Display requirements

| Platform | Tier 1 (Logic) | Tier 2 (Widget) | Tier 3 (Visual) |
|----------|:-:|:-:|:-:|
| POSIX local | Y | Y (needs `python-tk` brew package) | Y |
| Windows local | Y | Y (tkinter ships with Python) | Y |
| Linux CI (GitHub Actions) | Y | Y (with `xvfb-run`) | N |
| POSIX CI (GitHub Actions) | Y | Y (display available) | N |
| Windows CI (GitHub Actions) | Y | Y (GDI available) | N |
| uv venv (Homebrew Python) | Y | N (Tcl not in venv) | N |

### tkinter in uv venv

uv's standalone Python builds may lack Tcl runtime files. Fix: create the venv from Homebrew Python which includes `python-tk`:

```bash
brew install python@3.13 python-tk@3.13
uv venv --python /opt/homebrew/bin/python3.13 --clear .venv
uv sync --all-extras
```

After this, `uv run` has full tkinter access and GUI tests run via `just test-gui`.

On CI runners, tkinter ships with the system Python (Ubuntu, Windows) or is available via Quartz (POSIX). GUI tests self-skip when tkinter/Tcl is unavailable.

## Test Matrix — Tier 2 (Widget Integration)

### Screen: Welcome

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| W-01 | App starts on Welcome | `app._current_step == 0` | P0 |
| W-02 | Title "Mailpail" visible | Label with text contains "Mailpail" | P0 |
| W-03 | Get Started button exists | CTkButton with "Get Started" text | P0 |
| W-04 | Get Started advances to Login | After invoke, step == 1 | P0 |
| W-05 | Version number displayed | Label contains "Version" | P1 |
| W-06 | Nav buttons hidden on Welcome | Back/Next not visible | P1 |

### Screen: Login

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| L-01 | Email + password fields present | 2+ CTkEntry widgets | P0 |
| L-02 | Provider dropdown exists | CTkComboBox widget | P0 |
| L-03 | Test Connection button exists | CTkButton with text | P0 |
| L-04 | Browser Session button exists | CTkButton with text | P1 |
| L-05 | Reassurance text shown | Label contains "read-only" | P0 |
| L-06 | Next disabled without connection | `next_btn.cget("state") == "disabled"` | P0 |
| L-07 | Mock connection enables Next | After injecting mock client, state == "normal" | P0 |
| L-08 | Provider change updates state | After dropdown change, `_provider_key` updates | P1 |
| L-09 | Help link present | Label contains "app password" | P1 |
| L-10 | Empty submit shows error | Invoke Test Connection with empty fields | P1 |

### Screen: Folders

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| F-01 | Folder checkboxes render | 5+ CTkCheckBox after mock load | P0 |
| F-02 | INBOX pre-selected | INBOX checkbox text found | P0 |
| F-03 | Select All button works | All checkboxes checked after invoke | P0 |
| F-04 | Deselect All button works | All checkboxes unchecked after invoke | P1 |
| F-05 | AOL folder names correct | "Draft" (singular), "Bulk Mail" present | P0 |
| F-06 | No connection shows error | Without client, error label visible | P1 |

### Screen: Filters

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| FI-01 | 4 filter entries present | date_from, date_to, sender, subject | P0 |
| FI-02 | Unread checkbox present | CTkCheckBox with "nread" text | P1 |
| FI-03 | Skip Filters button exists | CTkButton with "Skip" | P0 |
| FI-04 | Skip advances to Format | After invoke, step == 4 | P0 |
| FI-05 | Invalid date blocks advance | "abc" in date_from, validate returns False | P1 |
| FI-06 | Valid date passes validation | "2024-01-01", validate returns True | P1 |
| FI-07 | build_filters populates state | After fill + validate, wizard_state has filters | P0 |

### Screen: Format

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| FM-01 | 6 format checkboxes | CSV, Excel, Excel-sheets, PDF, MBOX, EML | P0 |
| FM-02 | CSV checked by default | CSV checkbox variable == "on" | P0 |
| FM-03 | Output dir has Desktop default | Entry contains "Desktop" or "Mailpail" | P0 |
| FM-04 | Browse button exists | CTkButton with "Browse" | P1 |
| FM-05 | No format selected blocks advance | validate returns False with all unchecked | P0 |

### Screen: Progress

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| P-01 | Progress bar exists | CTkProgressBar widget | P0 |
| P-02 | Cancel button exists | CTkButton with "Cancel" | P0 |
| P-03 | Reassurance text shown | Label contains "safe" or "not" | P0 |
| P-04 | Log preview exists | CTkTextbox widget | P1 |

### Screen: Complete

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| C-01 | Email count displayed | Label contains mock count | P0 |
| C-02 | Open Folder button exists | CTkButton with "Open" | P0 |
| C-03 | Export Again button exists | CTkButton with "Export Again" | P0 |
| C-04 | Exit button exists | CTkButton with "Exit" | P0 |

### Navigation

| ID | Scenario | Assertion | Priority |
|----|----------|-----------|----------|
| N-01 | Back from Welcome stays | step remains 0 | P0 |
| N-02 | Next from Complete stays | step remains 6 | P0 |
| N-03 | Reset returns to Welcome | After reset, step == 0 | P0 |
| N-04 | Progress dots update | No crash iterating all 7 steps | P0 |
| N-05 | Invalid screen name is no-op | step unchanged | P1 |

## Execution

### Local (POSIX with Homebrew Python)

```bash
# Install tkinter support
brew install python-tk@3.13

# Run GUI tests with system Python
just test-gui

# Run visual smoke tests (screenshots to /tmp/mailpail_ui_test/)
/opt/homebrew/bin/python3.13 tests/test_ui_integration.py
```

### CI (GitHub Actions)

GUI tests run automatically in CI on platforms with display support:

| Runner | Display | GUI tests run? |
|--------|---------|:-:|
| `ubuntu-latest` | Xvfb (via `xvfb-run`) | Y |
| `macos-latest` | Quartz (native) | Y |
| `windows-latest` | GDI (native) | Y |

The `gui` pytest marker controls inclusion. Tests self-skip when tkinter/Tcl is unavailable.

### Adding new GUI tests

1. Add to `tests/tier_b/test_gui_integration.py`
2. Use the `app` fixture (creates + destroys MailpailApp per test)
3. Use `_pump(app, ms)` to process events after interactions
4. Use `_find_widgets(parent, "CTkClassName")` for widget discovery
5. Mark with `@pytest.mark.gui` (inherited from module-level `pytestmark`)
6. Test IDs follow the matrix above: `W-01`, `L-01`, `F-01`, etc.

## Coverage Gaps (backlog)

| Gap | Risk | When to address |
|-----|------|-----------------|
| No end-to-end GUI export (requires live IMAP mock) | Medium | When integration test infra matures |
| No dark mode rendering verification | Low | Post-1.0 when dark mode wired to UI |
| No multi-monitor/HiDPI testing | Low | Community-reported bugs only |
| No accessibility testing (screen reader compat) | Medium | Post-1.0, requires AT-SPI or similar |
| No localized string rendering tests | Low | When i18n implemented |
