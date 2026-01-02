# justfile for dsmr2mqtt

# Default recipe to display help information
default:
    @just --list

# Install dependencies
install:
    uv sync

# Install dev dependencies
install-dev:
    uv sync --all-groups

# Format code with ruff
format:
    uv run ruff format .

# Check formatting without making changes
format-check:
    uv run ruff format --check .

# Lint code with ruff
lint:
    uv run ruff check .

# Fix linting issues automatically
lint-fix:
    uv run ruff check --fix .

# Run type checking with mypy
typecheck:
    uv run mypy src/dsmr2mqtt

# Run all checks (format, lint, typecheck)
check: format-check lint typecheck

# Fix all auto-fixable issues
fix: format lint-fix

# Run the application in production mode
run:
    uv run dsmr2mqtt

# Run the application in simulation mode (no USB device required)
run-sim:
    DSMR_PRODUCTION=false uv run dsmr2mqtt

# Build Docker image
docker-build:
    docker build -t dsmr2mqtt:latest .

# Run Docker container in simulation mode
docker-run-sim:
    docker run --rm -e DSMR_PRODUCTION=false dsmr2mqtt:latest

# Run end-to-end tests with docker compose
e2e-test:
    docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test

# Clean up end-to-end test containers
e2e-clean:
    docker compose -f docker-compose.e2e.yml down -v

# Clean build artifacts and cache
clean:
    rm -rf .ruff_cache .mypy_cache __pycache__ .pytest_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
