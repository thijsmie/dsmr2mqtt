from paho.mqtt.client import MQTTv5, MQTTv31, MQTTv311

from .mqtt import MQTTClient as MQTTClient

__version__ = "2.0.0"
__author__ = "Hans IJntema"
__license__ = "GPLv3"

__all__ = ["MQTTClient", "MQTTv31", "MQTTv311", "MQTTv5"]
