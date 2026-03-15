default:
    @just --list

install:
    uv sync --all-extras

lint:
    uv run ruff check src/ tests/
    uv run ruff format --check src/ tests/

format:
    uv run ruff format src/ tests/
    uv run ruff check --fix src/ tests/

test:
    uv run pytest -n auto --cache-clear tests/

test-a:
    uv run pytest -n auto --cache-clear -m tier_a tests/

test-b:
    uv run pytest -n auto --cache-clear -m tier_b tests/

test-ci:
    mkdir -p reports
    uv run pytest -n auto --cache-clear --junitxml=reports/junit.xml --cov=mailpail --cov-report=xml:reports/coverage.xml tests/

build-exe:
    uv run pyinstaller --onefile --name mailpail --windowed src/mailpail/__main__.py

clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache reports/ __pycache__
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

all: format lint test
