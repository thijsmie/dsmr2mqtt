FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/thijsmie/dsmr2mqtt"
LABEL org.opencontainers.image.description="MQTT client for Belgian and Dutch Smart Meter (DSMR)"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY *.py ./
COPY log/ ./log/
COPY mqtt/ ./mqtt/
COPY test/ ./test/

# Install dependencies using uv
RUN uv sync --no-dev --no-install-project

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash dsmr && \
    chown -R dsmr:dsmr /app

USER dsmr

# Run the application
CMD ["uv", "run", "python", "dsmr-mqtt.py"]
