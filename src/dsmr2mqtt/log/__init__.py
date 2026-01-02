"""
Logging module for dsmr2mqtt.

Provides structured logging with JSON output for production
and human-readable console output for development.

Usage:
    from log import logger, stats_logger

    # Regular logging
    logger.info("event_name", key="value")

    # Statistics tracking
    stats_logger.increment("mqtt_messages_sent")
"""

from .structured_log import StatisticsLogger, get_logger, get_stats_logger

# Initialize the main logger
logger = get_logger("dsmr2mqtt")

# Statistics logger (lazy initialization)
stats_logger = get_stats_logger()

__version__ = "2.0.0"
__author__ = "Hans IJntema"
__license__ = "GPLv3"

__all__ = ["logger", "stats_logger", "get_logger", "get_stats_logger", "StatisticsLogger"]
