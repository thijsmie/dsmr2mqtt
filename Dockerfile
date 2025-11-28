FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/thijsmie/dsmr2mqtt"
LABEL org.opencontainers.image.description="MQTT client for Belgian and Dutch Smart Meter (DSMR)"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY *.py ./
COPY log/ ./log/
COPY mqtt/ ./mqtt/
COPY test/ ./test/

# Install dependencies using uv (frozen to ensure reproducibility)
RUN uv sync --frozen --no-dev --no-install-project

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash dsmr && \
    chown -R dsmr:dsmr /app

USER dsmr

# Environment variables with defaults
# MQTT Configuration
ENV MQTT_BROKER="192.168.1.1"
ENV MQTT_PORT="1883"
ENV MQTT_CLIENT_ID="mqtt-dsmr"
ENV MQTT_QOS="1"
ENV MQTT_USERNAME=""
ENV MQTT_PASSWORD=""
ENV MQTT_MAXRATE="60"
ENV MQTT_TOPIC_PREFIX="dsmr"

# Home Assistant Configuration
ENV HA_DISCOVERY="true"
ENV HA_DELETECONFIG="true"
ENV HA_DISCOVERY_RATE="12"

# Serial Port Configuration
ENV SERIAL_PORT="/dev/ttyUSB0"
ENV SERIAL_BAUDRATE="115200"

# Application Configuration
ENV DSMR_LOGLEVEL="INFO"
ENV DSMR_PRODUCTION="true"
ENV DSMR_SIMULATORFILE="test/dsmr.raw"

# Run the application
CMD ["uv", "run", "python", "dsmr-mqtt.py"]
