FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/thijsmie/dsmr2mqtt"
LABEL org.opencontainers.image.description="MQTT client for Belgian and Dutch Smart Meter (DSMR)"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"

WORKDIR /app

# Copy source files directly
COPY src/dsmr2mqtt /app/dsmr2mqtt
COPY test/ /app/test/

# Install dependencies directly without using pyproject.toml build
RUN pip install --no-cache-dir \
    paho-mqtt>=2.0.0 \
    pyserial>=3.5 \
    persist-queue>=0.8.0 \
    packaging>=23.0 \
    structlog>=25.0.0

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash dsmr && \
    chown -R dsmr:dsmr /app

USER dsmr

# Add the app directory to Python path
ENV PYTHONPATH=/app

# Environment variables with defaults
# MQTT Configuration
# Use MQTT_URL for URL-style configuration (mqtt://, mqtts://, ws://, wss://)
# If MQTT_URL is set, it takes precedence over MQTT_BROKER and MQTT_PORT
ENV MQTT_URL=""
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

# Run the application using python -m
CMD ["python", "-m", "dsmr2mqtt"]
