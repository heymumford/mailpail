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
    uv run python -m pytest -n auto --cache-clear tests/

test-a:
    uv run python -m pytest -n auto --cache-clear -m tier_a tests/

test-b:
    uv run python -m pytest -n auto --cache-clear -m tier_b tests/

test-gui:
    uv run python -m pytest --cache-clear -m gui tests/ --override-ini="addopts=-v --tb=short --ignore=tests/test_ui_integration.py"

test-live:
    uv run python -m pytest --cache-clear -m live tests/ --override-ini="addopts=-v --tb=long --ignore=tests/test_ui_integration.py" -s

test-e2e:
    uv run python -m pytest --cache-clear -m e2e tests/ --override-ini="addopts=-v --tb=long --ignore=tests/test_ui_integration.py"

test-ci:
    mkdir -p reports
    uv run python -m pytest -n auto --cache-clear --junitxml=reports/junit.xml --cov=mailpail --cov-report=xml:reports/coverage.xml tests/

build-exe:
    uv run pyinstaller --onefile --name mailpail --windowed src/mailpail/__main__.py

clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache reports/ __pycache__
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

all: format lint test
