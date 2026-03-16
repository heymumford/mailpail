# Contributing

## Dev Setup

1. Install [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just)
2. Fork and clone the repository
3. Install dependencies:

```bash
just install       # uv sync --all-extras
```

4. Verify your environment:

```bash
just all           # format + lint + test
```

> **Without just:** All recipes delegate to `uv run`. See `justfile` for the underlying commands (e.g., `uv run pytest -n auto --cache-clear -m tier_a tests/`).

## Running Tests

```bash
just test          # all tests
just test-a        # Tier A only
just test-b        # Tier B only
just lint          # ruff check + format check
just format        # auto-fix formatting and lint
```

### Test Tiers

| Tier | Command | Scope | CI Gate |
|------|---------|-------|---------|
| **A** | `just test-a` | Must-pass product feature scenarios. These validate core user-facing behavior: IMAP download, export formats, wizard flow. A Tier A failure blocks merge. | Required on all OS + Python matrix |
| **B** | `just test-b` | Regression and edge case tests. These cover boundary conditions, error handling, and non-critical paths. Tier B failures should be investigated but do not block merge in isolation. | Required on Ubuntu, Python 3.12+3.13 |

New features require Tier A tests. Bug fixes require a Tier B regression test that reproduces the bug.

## Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-change`
3. Make your changes
4. Run the full quality gate: `just all` (includes format, lint, and all tests)
5. Commit with a meaningful message (why, not what)
6. Push your branch and open a pull request

## Standards

- Python 3.12+, type hints on all public functions
- `ruff` for linting and formatting (line length 120)
- Tests must be parallelizable (no shared state between tests)
- Include SPDX license headers in new source files:
  ```python
  # SPDX-License-Identifier: GPL-3.0-or-later
  ```

## Pull Request Process

1. Fill in the PR description: what changed and why
2. Verify CI passes (the badge on your PR will show status)
3. Address review feedback with fixup commits, then squash before merge

### PR Checklist

- [ ] `just all` passes (format + lint + all tests including Tier A)
- [ ] New features have corresponding Tier A tests
- [ ] Bug fixes have a Tier B regression test
- [ ] No credentials or secrets in the diff
- [ ] SPDX header on new source files

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0-or-later license.
