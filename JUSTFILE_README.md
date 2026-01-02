# Justfile for dsmr2mqtt

This project includes a `justfile` for common development tasks. [Just](https://github.com/casey/just) is a command runner similar to `make` but simpler and cross-platform.

## Installation

Install just using one of these methods:

```bash
# macOS
brew install just

# Linux (cargo)
cargo install just

# Or download from https://github.com/casey/just/releases
```

## Available Commands

List all available commands:
```bash
just
```

### Development

```bash
# Install dependencies
just install

# Install dev dependencies  
just install-dev

# Format code with ruff
just format

# Check formatting without making changes
just format-check

# Lint code with ruff
just lint

# Fix linting issues automatically
just lint-fix

# Run type checking with mypy
just typecheck

# Run all checks (format, lint, typecheck)
just check

# Fix all auto-fixable issues
just fix
```

### Running

```bash
# Run the application in production mode
just run

# Run the application in simulation mode (no USB device required)
just run-sim
```

### Docker

```bash
# Build Docker image
just docker-build

# Run Docker container in simulation mode
just docker-run-sim
```

### Testing

```bash
# Run end-to-end tests with docker compose
just e2e-test

# Clean up end-to-end test containers
just e2e-clean
```

### Cleanup

```bash
# Clean build artifacts and cache
just clean
```
