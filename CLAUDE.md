# AOL Email Exporter

## Build
- `just install` -- set up environment
- `just test` -- run all tests parallel
- `just test-a` -- tier A (must-pass features)
- `just test-b` -- tier B (regression)
- `just lint` -- check code style
- `just format` -- fix code style
- `just build-exe` -- build Windows executable

## Architecture
- `src/aol_email_exporter/` -- application code
  - `ui/` -- customtkinter wizard interface
  - `exporters/` -- CSV, Excel, PDF exporters
  - `client.py` -- IMAP client
  - `cookie_auth.py` -- browser cookie detection
- `tests/tier_a/` -- must-pass product feature tests
- `tests/tier_b/` -- regression tests

## Rules
- ALWAYS use `just` recipes, never raw pytest/ruff
- Tests must be parallelizable (no shared state)
- GUI is default entry point; `--cli` flag for headless mode
- GPL-3.0 -- include SPDX header in new source files
