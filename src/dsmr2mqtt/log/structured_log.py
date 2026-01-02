"""
Structured logging module using structlog.

Provides JSON-formatted logs for production environments and
human-readable console output for development.

Configuration via environment variables:
  - DSMR_LOGLEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
  - DSMR_LOG_FORMAT: JSON or TEXT (default: JSON)
  - DSMR_STATS_LOG_INTERVAL: Interval in seconds for statistics logging (default: 300)

Usage:
    from log import logger, stats_logger

    # Regular logging
    logger.info("event_name", key="value")

    # Statistics tracking
    stats_logger.increment("mqtt_messages_sent")

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

import logging
import os
import sys
import threading
import time

import structlog
from structlog.typing import Processor


def _get_log_level(level_str: str) -> int:
    """Convert log level string to logging constant."""
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_str.upper(), logging.INFO)


def _get_log_format() -> str:
    """Get log format from environment variable."""
    return os.environ.get("DSMR_LOG_FORMAT", "JSON").upper()


def _get_log_level_str() -> str:
    """Get log level from environment variable."""
    return os.environ.get("DSMR_LOGLEVEL", "INFO").upper()


def setup_logging() -> structlog.stdlib.BoundLogger:
    """
    Configure and return a structured logger.

    Returns:
        structlog.stdlib.BoundLogger: Configured logger instance
    """
    log_format = _get_log_format()
    log_level = _get_log_level(_get_log_level_str())

    # Shared processors for both JSON and console output
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "JSON":
        # JSON format for production - structured logging
        final_processor: Processor = structlog.processors.JSONRenderer()
    else:
        # Console format for development - human-readable
        final_processor = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure formatter for stdlib logging integration
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            final_processor,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Configure standard library logging to integrate with structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence overly verbose loggers
    logging.getLogger("paho.mqtt").setLevel(logging.WARNING)

    return structlog.get_logger()


class StatisticsLogger:
    """
    Logs statistics at configurable intervals.

    Tracks and logs metrics about the application's operation,
    such as telegrams processed, MQTT messages sent, and errors.
    """

    def __init__(self, logger: structlog.stdlib.BoundLogger, interval: int = 300):
        """
        Initialize the statistics logger.

        Args:
            logger: The structlog logger to use
            interval: Logging interval in seconds (0 to disable)
        """
        self._logger = logger
        self._interval = interval
        self._stats: dict[str, int] = {
            "telegrams_received": 0,
            "telegrams_parsed": 0,
            "mqtt_messages_sent": 0,
            "mqtt_errors": 0,
            "parse_errors": 0,
            "serial_errors": 0,
        }
        self._lock = threading.Lock()
        self._last_log_time = time.time()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the statistics logging thread."""
        if self._interval <= 0:
            self._logger.info("statistics_logging_disabled")
            return

        self._running = True
        self._thread = threading.Thread(target=self._log_periodically, daemon=True)
        self._thread.start()
        self._logger.info(
            "statistics_logging_started",
            interval_seconds=self._interval,
        )

    def stop(self) -> None:
        """Stop the statistics logging thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self._log_stats()  # Final log on shutdown

    def increment(self, stat_name: str, count: int = 1) -> None:
        """
        Increment a statistic counter.

        Args:
            stat_name: Name of the statistic to increment
            count: Amount to increment by (default: 1)
        """
        with self._lock:
            if stat_name in self._stats:
                self._stats[stat_name] += count

    def _log_periodically(self) -> None:
        """Background thread that logs statistics periodically."""
        while self._running:
            time.sleep(1)  # Check every second for shutdown
            current_time = time.time()
            if current_time - self._last_log_time >= self._interval:
                self._log_stats()
                self._last_log_time = current_time

    def _log_stats(self) -> None:
        """Log current statistics."""
        with self._lock:
            stats_copy = self._stats.copy()

        self._logger.info(
            "statistics",
            **stats_copy,
        )


# Module-level logger instance
_logger: structlog.stdlib.BoundLogger | None = None
_stats_logger: StatisticsLogger | None = None


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Optional logger name for context

    Returns:
        Configured structlog logger
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()

    if name:
        return _logger.bind(logger=name)
    return _logger


def get_stats_logger() -> StatisticsLogger:
    """
    Get the statistics logger instance.

    Returns:
        StatisticsLogger instance
    """
    global _stats_logger, _logger
    if _stats_logger is None:
        if _logger is None:
            _logger = setup_logging()

        # Get interval from environment variable directly to avoid circular import with config
        interval_str = os.environ.get("DSMR_STATS_LOG_INTERVAL", "300")
        try:
            interval = int(interval_str)
        except ValueError:
            interval = 300

        _stats_logger = StatisticsLogger(_logger, interval)

    return _stats_logger
