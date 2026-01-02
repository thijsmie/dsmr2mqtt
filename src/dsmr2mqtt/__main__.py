#!/usr/bin/env python3

"""
DESCRIPTION
  Read DSMR (Dutch Smart Meter Requirements) smart energy meter via P1 USB cable
  Tested on raspberry pi4

4 Worker threads:
  - P1 USB serial port reader
  - DSMR telegram parser to MQTT messages
  - MQTT client
  - HA Discovery

Only dsmr v50 is implemented; other versions can be supported by adapting dsmr50.py


        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import os
import signal
import socket
import sys
import threading
import time

from dsmr2mqtt import __version__
from dsmr2mqtt import config as cfg
from dsmr2mqtt import hadiscovery as ha
from dsmr2mqtt import mqtt as mqtt
from dsmr2mqtt import p1_parser as convert
from dsmr2mqtt import p1_serial as p1
from dsmr2mqtt.log import logger, stats_logger

# DEFAULT exit code
# status=1/FAILURE
__exit_code = 1

# ------------------------------------------------------------------------------------
# Instance running?
# ------------------------------------------------------------------------------------
script = os.path.basename(__file__)
script = os.path.splitext(script)[0]

# Ensure that only one instance is started
if sys.platform == "linux":
    lockfile = "\0" + script + "_lockfile"
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # Create an abstract socket, by prefixing it with null.
        s.bind(lockfile)
        logger.info("application_started", file=__file__, version=__version__)
    except OSError as err:
        logger.error("instance_already_running", lockfile=lockfile, error=str(err))
        sys.exit(1)


def close():
    """Close the application gracefully."""
    # Stop statistics logging
    stats_logger.stop()
    logger.info("application_exiting", exit_code=__exit_code)
    sys.exit(__exit_code)


# ------------------------------------------------------------------------------------
# LATE GLOBALS
# ------------------------------------------------------------------------------------
trigger = threading.Event()
t_threads_stopper = threading.Event()
t_mqtt_stopper = threading.Event()

# mqtt thread
t_mqtt = mqtt.MQTTClient(
    mqtt_broker=cfg.MQTT_BROKER,
    mqtt_port=cfg.MQTT_PORT,
    mqtt_client_id=cfg.MQTT_CLIENT_UNIQ,
    mqtt_qos=cfg.MQTT_QOS,
    mqtt_cleansession=True,
    mqtt_protocol=mqtt.MQTTv5,
    username=cfg.MQTT_USERNAME,
    password=cfg.MQTT_PASSWORD,
    mqtt_stopper=t_mqtt_stopper,
    worker_threads_stopper=t_threads_stopper,
    transport=cfg.MQTT_TRANSPORT,
    use_tls=cfg.MQTT_USE_TLS,
    ws_path=cfg.MQTT_WS_PATH,
)

# SerialPort thread
telegram: list = []
t_serial = p1.TaskReadSerial(trigger, t_threads_stopper, telegram)

# Telegram parser thread
t_parse = convert.ParseTelegrams(trigger, t_threads_stopper, t_mqtt, telegram)

# Send Home Assistant auto discovery MQTT's
t_discovery = ha.Discovery(t_threads_stopper, t_mqtt, __version__)


def exit_gracefully(signal, stackframe):
    """Exit gracefully on signal.

    Args:
        signal: the associated signalnumber
        stackframe: current stack frame
    """
    logger.debug("signal_received", signal=signal)

    # status=0/SUCCESS
    global __exit_code
    __exit_code = 0

    t_threads_stopper.set()
    logger.info("graceful_shutdown_initiated")


def main():
    """Main entry point for the application."""
    logger.debug("main_started")

    # Start statistics logging
    stats_logger.start()

    logger.info(
        "configuration_loaded",
        serial_port=cfg.ser_port,
        mqtt_maxrate=cfg.MQTT_MAXRATE,
        stats_interval=cfg.STATS_LOG_INTERVAL,
    )

    # Set last will/testament
    t_mqtt.will_set(
        cfg.MQTT_TOPIC_PREFIX + "/status", payload="offline", qos=cfg.MQTT_QOS, retain=True
    )

    # Start all threads
    t_mqtt.start()
    # Introduce a small delay before starting the parsing, otherwise initial messages cannot be published
    time.sleep(1)
    t_parse.start()
    t_discovery.start()
    t_serial.start()

    # Set status to online
    t_mqtt.set_status(cfg.MQTT_TOPIC_PREFIX + "/status", "online", retain=True)
    logger.debug("meter_status_updated", status="online")
    t_mqtt.do_publish(
        cfg.MQTT_TOPIC_PREFIX + "/sw-version",
        f"main={__version__}; mqtt={mqtt.__version__}",
        retain=True,
    )

    # block till t_serial stops receiving telegrams/exits
    t_serial.join()
    logger.debug("serial_thread_exited")
    t_threads_stopper.set()

    # Set status to offline
    t_mqtt.set_status(cfg.MQTT_TOPIC_PREFIX + "/status", "offline", retain=True)
    logger.debug("meter_status_updated", status="offline")

    # Todo check if MQTT queue is empty before setting stopper
    # Use a simple delay of 1sec before closing mqtt
    time.sleep(1)
    t_mqtt_stopper.set()

    logger.debug("main_completed")
    return


# ------------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------------
if __name__ == "__main__":
    logger.debug("entrypoint_started")
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    # start main program
    main()

    logger.debug("entrypoint_completed")
    close()
