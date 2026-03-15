# Contributing

## Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-change`
3. Make your changes
4. Run the full quality gate: `just all`
5. Ensure all Tier A tests pass: `just test-a`
6. Commit with a meaningful message (why, not what)
7. Push your branch and open a pull request

## Standards

- Python 3.12+, type hints on all public functions
- `ruff` for linting and formatting (line length 120)
- Tests must be parallelizable (no shared state between tests)
- Include SPDX license headers in new source files:
  ```python
  # SPDX-License-Identifier: GPL-3.0-or-later
  ```

## Pull Request Checklist

- [ ] `just all` passes (format + lint + test)
- [ ] Tier A tests pass
- [ ] New features have corresponding tests
- [ ] No credentials or secrets in the diff

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0-or-later license.
