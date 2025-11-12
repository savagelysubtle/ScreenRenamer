"""Tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from screenrenamer.config import ScreenRenamerConfig, WatcherConfig


def test_default_config():
    """Test default configuration creation."""
    config = ScreenRenamerConfig.from_env()

    assert isinstance(config.watcher.watch_path, Path)
    assert config.llm.model_name == "llama3.2-vision:11b"
    assert config.llm.base_url == "http://localhost:11434"
    assert config.watcher.patterns == ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff"]


def test_config_with_env_vars():
    """Test configuration with environment variables."""
    env_vars = {
        "SCREENRENAMER_WATCH_PATH": "/tmp/screenshots",
        "SCREENRENAMER_LLM_MODEL": "custom-model",
        "SCREENRENAMER_LLM_URL": "http://custom:8080",
        "SCREENRENAMER_LLM_TIMEOUT": "60",
    }

    with patch.dict(os.environ, env_vars):
        config = ScreenRenamerConfig.from_env()

        assert str(config.watcher.watch_path) == "/tmp/screenshots"
        assert config.llm.model_name == "custom-model"
        assert config.llm.base_url == "http://custom:8080"
        assert config.llm.timeout == 60


def test_watcher_config_validation():
    """Test watcher configuration validation."""
    # Valid path
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.is_dir", return_value=True):
        config = WatcherConfig(watch_path=Path("/valid/path"))
        assert config.watch_path == Path("/valid/path")

    # Invalid path (doesn't exist)
    with patch("pathlib.Path.exists", return_value=False), \
         pytest.raises(ValueError, match="Watch path does not exist"):
        WatcherConfig(watch_path=Path("/invalid/path"))

    # Path exists but is not a directory
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.is_dir", return_value=False), \
         pytest.raises(ValueError, match="Watch path is not a directory"):
        WatcherConfig(watch_path=Path("/file/not/dir"))
