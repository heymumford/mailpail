# Mailpail

## Build
- `just install` -- set up environment
- `just test` -- run all tests parallel (100 tests)
- `just test-a` -- tier A (must-pass features)
- `just test-b` -- tier B (regression + fitness + persona)
- `just lint` -- check code style
- `just format` -- fix code style
- `just build-exe` -- build Windows executable

## Architecture
- `src/mailpail/` -- application code
  - `auth.py` -- AuthFlow Protocol, Credential, Capability flags, AppPasswordFlow
  - `credentials.py` -- CredentialStore Protocol (env, memory, file stores)
  - `plugin.py` -- entry-point-based plugin discovery (`mailpail.providers`)
  - `providers.py` -- ProviderDescriptor, EmailProvider Protocol, 5 built-in providers
  - `client.py` -- IMAPClient (built-in adapter)
  - `cookie_auth.py` -- browser cookie detection
  - `models.py` -- EmailRecord, FilterParams, ExportConfig, ExportResult
  - `filters.py` -- client-side email filtering
  - `exporters/` -- CSV, Excel, PDF exporters
  - `ui/` -- customtkinter wizard interface
    - `screens/` -- 7 wizard screens + BaseScreen skeleton
    - `theme.py` -- colors, fonts, icons (WCAG AA compliant)
    - `strings.py` -- all user-visible text centralized
- `tests/tier_a/` -- must-pass product feature tests
- `tests/tier_b/` -- regression, fitness, persona tests

## Rules
- ALWAYS use `just` recipes, never raw pytest/ruff
- Tests must be parallelizable (no shared state)
- GUI is default entry point; `--cli` flag for headless mode
- GPL-3.0 -- include SPDX header in new source files
- No hardcoded hex colors in screen files (use theme.py)
- No "AOL" in user-visible strings (use strings.py)
- No fade_in animation (removed for ghost rendering fix)
- Provider registry is open for extension via entry points
