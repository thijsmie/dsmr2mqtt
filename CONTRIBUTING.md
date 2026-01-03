# Contributing to dsmr2mqtt

Thank you for your interest in contributing to dsmr2mqtt! This document provides guidelines for development.

## Development Setup

### Prerequisites

- Python 3.12 or later
- [just](https://github.com/casey/just) (optional, but recommended)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/thijsmie/dsmr2mqtt.git
   cd dsmr2mqtt
   ```

2. Install dependencies:
   ```bash
   # Using uv (recommended)
   uv sync --all-groups

   # Or using pip
   pip install -e ".[dev]"
   ```

3. Install development tools:
   ```bash
   pip install ruff mypy
   ```

## Code Quality

This project uses modern Python tools to maintain code quality:

- **ruff**: For code formatting and linting
- **mypy**: For static type checking

### Before Committing

Always run these checks before committing:

```bash
# Using just
just check

# Or manually
ruff format src/
ruff check src/
mypy src/dsmr2mqtt
```

### Auto-fixing Issues

Many issues can be automatically fixed:

```bash
# Using just
just fix

# Or manually
ruff format src/
ruff check --fix src/
```

## Code Style

- Follow PEP 8 guidelines (enforced by ruff)
- Use type hints where possible
- Keep line length to 100 characters
- Use descriptive variable names
- Add docstrings to public functions and classes

## Package Structure

The project uses a `src/` layout:

```
dsmr2mqtt/
├── src/
│   └── dsmr2mqtt/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── dsmr50.py
│       ├── hadiscovery.py
│       ├── p1_parser.py
│       ├── p1_serial.py
│       ├── log/
│       │   ├── __init__.py
│       │   └── structured_log.py
│       └── mqtt/
│           ├── __init__.py
│           └── mqtt.py
├── test/
│   ├── dsmr.raw
│   └── mosquitto.conf
├── pyproject.toml
├── justfile
└── docker-compose.e2e.yml
```

## Testing

### End-to-End Tests

Run the full end-to-end test suite with Docker Compose:

```bash
# Using just
just e2e-test

# Or manually
docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from test
```

This will:
1. Start a Mosquitto MQTT broker
2. Create a virtual USB device with DSMR data
3. Run the dsmr2mqtt application
4. Verify that MQTT messages are published correctly

### Manual Testing

Run the application in simulation mode without a physical device:

```bash
# Using just
just run-sim

# Or manually
DSMR_PRODUCTION=false MQTT_BROKER=localhost dsmr2mqtt
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Run all checks: `just check`
4. Update documentation if needed
5. Create a pull request with a clear description
6. Wait for CI checks to pass
7. Address any review comments

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Formatting check**: Ensures code is properly formatted
- **Linting**: Checks for code quality issues
- **Type checking**: Validates type hints
- **E2E tests**: Runs end-to-end tests with Docker
- **Docker build**: Builds and publishes Docker images

All checks must pass before a PR can be merged.

## Questions?

If you have questions or need help, please open an issue on GitHub.
