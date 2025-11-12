"""Logging configuration and utilities for ScreenRenamer."""

import logging
import sys
from pathlib import Path

from .config import LoggingConfig, get_config


class ScreenRenamerLogger:
    """Custom logger for ScreenRenamer with structured output."""

    def __init__(self, name: str = "screenrenamer"):
        self.name = name
        self._logger: logging.Logger | None = None

    def _setup_logger(self, config: LoggingConfig) -> logging.Logger:
        """Set up the logger with the given configuration."""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(config.format)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if specified)
        if config.file_path:
            try:
                config.file_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(config.file_path)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except OSError as e:
                # If file logging fails, log to console only
                logger.warning(f"Failed to set up file logging to {config.file_path}: {e}")

        return logger

    @property
    def logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        if self._logger is None:
            config = get_config().logging
            self._logger = self._setup_logger(config)
        return self._logger

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)

    def log_file_event(self, event_type: str, file_path: Path, details: str | None = None) -> None:
        """Log a file-related event."""
        message = f"File {event_type}: {file_path.name}"
        if details:
            message += f" ({details})"
        self.info(message)

    def log_llm_event(self, action: str, model: str, success: bool, details: str | None = None) -> None:
        """Log an LLM-related event."""
        status = "SUCCESS" if success else "FAILED"
        message = f"LLM {action} ({model}): {status}"
        if details:
            message += f" - {details}"
        if success:
            self.info(message)
        else:
            self.error(message)

    def log_rename_event(self, old_path: Path, new_path: Path, success: bool, details: str | None = None) -> None:
        """Log a file rename event."""
        if success:
            self.info(f"Renamed: {old_path.name} -> {new_path.name}")
        else:
            self.error(f"Failed to rename {old_path.name}: {details}")


# Global logger instance
_logger: ScreenRenamerLogger | None = None


def get_logger(name: str = "screenrenamer") -> ScreenRenamerLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None or _logger.name != name:
        _logger = ScreenRenamerLogger(name)
    return _logger


def setup_logging(config: LoggingConfig) -> None:
    """Set up logging globally."""
    logger = get_logger()
    logger._logger = logger._setup_logger(config)
