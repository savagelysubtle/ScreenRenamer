"""Tests for logger.py."""

import logging
import sys
from pathlib import Path

from screenrenamer.config import LoggingConfig
from screenrenamer.logger import ScreenRenamerLogger, get_logger, setup_logging


class TestScreenRenamerLogger:
    """Test the ScreenRenamerLogger class."""

    def test_init_default(self, temp_dir):
        """Test initialization with default name."""
        logger = ScreenRenamerLogger()

        assert logger.name == "screenrenamer"
        assert logger._logger is None

    def test_init_custom_name(self, temp_dir):
        """Test initialization with custom name."""
        logger = ScreenRenamerLogger("custom")

        assert logger.name == "custom"

    def test_setup_logger_console_only(self, temp_dir):
        """Test logger setup with console output only."""
        config = LoggingConfig(level="INFO", format="%(levelname)s: %(message)s")

        logger_instance = ScreenRenamerLogger._setup_logger_static(config)

        assert logger_instance.level == logging.INFO
        assert len(logger_instance.handlers) == 1  # Console handler only

        # Check console handler
        console_handler = logger_instance.handlers[0]
        assert isinstance(console_handler, logging.StreamHandler)
        assert console_handler.stream == sys.stdout

    def test_setup_logger_with_file(self, temp_dir):
        """Test logger setup with file output."""
        log_file = temp_dir / "test.log"
        config = LoggingConfig(level="DEBUG", file_path=log_file, format="%(asctime)s %(message)s")

        logger_instance = ScreenRenamerLogger._setup_logger_static(config)

        assert len(logger_instance.handlers) == 2  # Console + file

        # Check file handler
        file_handler = logger_instance.handlers[1]
        assert isinstance(file_handler, logging.FileHandler)
        assert file_handler.baseFilename == str(log_file)

    def test_setup_logger_file_creation_error(self, temp_dir):
        """Test handling of file creation errors."""
        invalid_path = Path("/invalid/path/test.log")
        config = LoggingConfig(file_path=invalid_path)

        # Should not raise exception, just log warning
        logger_instance = ScreenRenamerLogger._setup_logger_static(config)

        # Should still have console handler
        assert len(logger_instance.handlers) == 1

    def test_property_logger_caching(self, temp_dir):
        """Test that logger property caches the instance."""
        logger = ScreenRenamerLogger("test")

        first_call = logger.logger
        second_call = logger.logger

        assert first_call is second_call
        assert first_call is logger._logger

    def test_log_methods(self, temp_dir, caplog):
        """Test all logging level methods."""
        logger = ScreenRenamerLogger("test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")

        assert "debug message" in caplog.text
        assert "info message" in caplog.text
        assert "warning message" in caplog.text
        assert "error message" in caplog.text
        assert "critical message" in caplog.text

    def test_log_file_event(self, temp_dir, caplog):
        """Test file event logging."""
        logger = ScreenRenamerLogger("test")

        test_file = temp_dir / "test.png"

        with caplog.at_level(logging.INFO):
            logger.log_file_event("created", test_file)
            logger.log_file_event("modified", test_file, "additional details")

        assert "File created: test.png" in caplog.text
        assert "File modified: test.png (additional details)" in caplog.text

    def test_log_llm_event_success(self, temp_dir, caplog):
        """Test successful LLM event logging."""
        logger = ScreenRenamerLogger("test")

        with caplog.at_level(logging.INFO):
            logger.log_llm_event("generation", "test-model", True, "Generated filename")

        assert "SUCCESS" in caplog.text
        assert "Generated filename" in caplog.text

    def test_log_llm_event_failure(self, temp_dir, caplog):
        """Test failed LLM event logging."""
        logger = ScreenRenamerLogger("test")

        with caplog.at_level(logging.ERROR):
            logger.log_llm_event("generation", "test-model", False, "API error")

        assert "FAILED" in caplog.text
        assert "API error" in caplog.text

    def test_log_rename_event_success(self, temp_dir, caplog):
        """Test successful rename event logging."""
        logger = ScreenRenamerLogger("test")

        old_file = temp_dir / "old.png"
        new_file = temp_dir / "new.png"

        with caplog.at_level(logging.INFO):
            logger.log_rename_event(old_file, new_file, True)

        assert "Renamed: old.png -> new.png" in caplog.text

    def test_log_rename_event_failure(self, temp_dir, caplog):
        """Test failed rename event logging."""
        logger = ScreenRenamerLogger("test")

        old_file = temp_dir / "old.png"
        failed_file = Path("FAILED")

        with caplog.at_level(logging.ERROR):
            logger.log_rename_event(old_file, failed_file, False, "Permission denied")

        assert "Failed to rename old.png: Permission denied" in caplog.text


def test_get_logger_singleton():
    """Test logger singleton behavior."""
    logger1 = get_logger("test")
    logger2 = get_logger("test")

    assert logger1 is logger2

    # Different name should create different instance
    logger3 = get_logger("different")
    assert logger3 is not logger1


def test_get_logger_default_name():
    """Test get_logger with default name."""
    logger1 = get_logger()
    logger2 = get_logger("screenrenamer")

    assert logger1 is logger2


def test_setup_logging():
    """Test global logging setup."""
    config = LoggingConfig(level="WARNING", format="TEST: %(message)s")

    setup_logging(config)

    # Get the global logger
    logger = get_logger()
    assert logger._logger.level == logging.WARNING
