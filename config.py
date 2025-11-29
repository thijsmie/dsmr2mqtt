"""
  Configuration for dsmr2mqtt

  This module reads configuration from environment variables with sensible defaults.
  For Docker deployments, set environment variables instead of editing this file.

  Configure:
  - MQTT client
  - Home Assistant Discovery
  - USB P1 serial port
  - Debug level

  Configure the DSMR messages in dsmr50.py

"""

import os
from urllib.parse import urlparse


def _get_bool_env(name, default):
    """Get boolean value from environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def _get_int_env(name, default):
    """Get integer value from environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_mqtt_url(url):
    """
    Parse an MQTT URL and return connection parameters.

    Supported URL schemes:
    - mqtt://host:port - TCP connection (default port 1883)
    - mqtts://host:port - TCP with TLS connection (default port 8883)
    - ws://host:port/path - WebSocket connection (default port 80)
    - wss://host:port/path - WebSocket Secure connection (default port 443)

    Returns:
        tuple: (host, port, transport, use_tls, path)
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    # Map scheme to transport and defaults
    scheme_config = {
        'mqtt': {'transport': 'tcp', 'default_port': 1883, 'use_tls': False},
        'mqtts': {'transport': 'tcp', 'default_port': 8883, 'use_tls': True},
        'ws': {'transport': 'websockets', 'default_port': 80, 'use_tls': False},
        'wss': {'transport': 'websockets', 'default_port': 443, 'use_tls': True},
    }

    if scheme not in scheme_config:
        raise ValueError(f"Unsupported MQTT URL scheme: {scheme}. "
                         f"Supported schemes: mqtt://, mqtts://, ws://, wss://")

    config = scheme_config[scheme]
    host = parsed.hostname or '192.168.1.1'
    port = parsed.port or config['default_port']
    path = parsed.path if parsed.path else None

    return host, port, config['transport'], config['use_tls'], path


# [ LOGLEVELS ]
# DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = os.environ.get("DSMR_LOGLEVEL", "INFO")

# [ LOG FORMAT ]
# JSON for structured JSON logs, TEXT for human-readable console logs
LOG_FORMAT = os.environ.get("DSMR_LOG_FORMAT", "JSON")

# [ STATISTICS LOGGING INTERVAL ]
# Interval in seconds for logging statistics (default: 300 = 5 minutes)
# Set to 0 to disable statistics logging
STATS_LOG_INTERVAL = _get_int_env("DSMR_STATS_LOG_INTERVAL", 300)

# [ PRODUCTION ]
# True if run in production
# False when running in simulation
PRODUCTION = _get_bool_env("DSMR_PRODUCTION", True)

# File below is used when PRODUCTION is set to False
# Simulation file can be created in bash/Linux:
# tail -f /dev/ttyUSB0 > dsmr.raw (wait 10-15sec and hit ctrl-C)
# (assuming that P1 USB is connected as ttyUSB0)
# Add string "EOF" (without quotes) as last line
SIMULATORFILE = os.environ.get("DSMR_SIMULATORFILE", "test/dsmr.raw")

# [ MQTT Parameters ]
# MQTT_URL: Use URL-style configuration for MQTT connections
# Supported schemes:
# - mqtt://host:port - TCP connection (default port 1883)
# - mqtts://host:port - TCP with TLS (default port 8883)
# - ws://host:port/path - WebSocket connection (default port 80)
# - wss://host:port/path - WebSocket Secure connection (default port 443)
# If MQTT_URL is not set, MQTT_BROKER and MQTT_PORT are used for backward compatibility
MQTT_URL = os.environ.get("MQTT_URL", "")

# Legacy broker configuration (used when MQTT_URL is not set)
# Using local dns names is not always reliable with PAHO
_MQTT_BROKER_DEFAULT = os.environ.get("MQTT_BROKER", "192.168.1.1")
_MQTT_PORT_DEFAULT = _get_int_env("MQTT_PORT", 1883)

# Parse MQTT URL or use legacy configuration
if MQTT_URL:
    MQTT_BROKER, MQTT_PORT, MQTT_TRANSPORT, MQTT_USE_TLS, MQTT_WS_PATH = _parse_mqtt_url(MQTT_URL)
else:
    MQTT_BROKER = _MQTT_BROKER_DEFAULT
    MQTT_PORT = _MQTT_PORT_DEFAULT
    MQTT_TRANSPORT = "tcp"
    MQTT_USE_TLS = False
    MQTT_WS_PATH = None

MQTT_CLIENT_UNIQ_ID = os.environ.get("MQTT_CLIENT_ID", "mqtt-dsmr")
MQTT_QOS = _get_int_env("MQTT_QOS", 1)
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

# MAX number of MQTT messages per hour. Assumption is that incoming messages are evenly spread in time
# EXAMPLE 1: 1 per hour, 12: every 5min, 60: every 1min, 720; every 5sec, 3600: every 1sec
# Actual rate will never be higher than P1 dsmr message rate
# MQTT_MAXRATE = [1..3600]
MQTT_MAXRATE = _get_int_env("MQTT_MAXRATE", 60)

# MQTT topic prefix
MQTT_TOPIC_PREFIX = os.environ.get("MQTT_TOPIC_PREFIX", "dsmr")

if PRODUCTION:
    MQTT_CLIENT_UNIQ = MQTT_CLIENT_UNIQ_ID
    HA_ID = ""
else:
    # In non-production mode, use test prefix
    if MQTT_TOPIC_PREFIX == "dsmr":
        MQTT_TOPIC_PREFIX = "test_dsmr"
    MQTT_CLIENT_UNIQ = "mqtt-dsmr-test"
    HA_ID = "TEST"

# [ Home Assistant ]
HA_DISCOVERY = _get_bool_env("HA_DISCOVERY", True)

# Default is False, removes the auto config message when this program exits
HA_DELETECONFIG = _get_bool_env("HA_DELETECONFIG", True)

# Discovery messages per hour
# At start-up, always a discovery message is send
# Default is 12 ==> 1 message every 5 minutes. If the MQTT broker is restarted
# it can take up to 5 minutes before the dsmr device re-appears in HA
HA_DISCOVERY_RATE = _get_int_env("HA_DISCOVERY_RATE", 12)

# [ P1 USB serial ]
ser_port = os.environ.get("SERIAL_PORT", "/dev/ttyUSB0")
ser_baudrate = _get_int_env("SERIAL_BAUDRATE", 115200)
