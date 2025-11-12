"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from screenrenamer.config import LLMConfig, RenamerConfig, ScreenRenamerConfig, WatcherConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_image_path(temp_dir):
    """Create a sample image file for testing."""
    image_path = temp_dir / "test_screenshot.png"
    # Create a minimal PNG file (just the PNG signature)
    png_signature = b"\x89PNG\r\n\x1a\n"
    image_path.write_bytes(png_signature)
    return image_path


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration for testing."""
    watcher_config = WatcherConfig(watch_path=temp_dir)
    llm_config = LLMConfig(
        model_name="test-model",
        base_url="http://test:8080",
        timeout=30,
        temperature=0.1,
        max_tokens=100,
    )
    renamer_config = RenamerConfig()

    config = ScreenRenamerConfig(llm=llm_config, watcher=watcher_config, renamer=renamer_config)
    return config


@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client for testing."""
    mock_client = MagicMock()

    # Mock the list method
    mock_model = MagicMock()
    mock_model.model = "test-model"
    mock_models = MagicMock()
    mock_models.models = [mock_model]
    mock_client.list.return_value = mock_models

    # Mock the chat method
    mock_response = MagicMock()
    mock_response.message.content = "test_filename"
    mock_client.chat.return_value = mock_response

    return mock_client


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before each test."""
    # Store original values
    original_env = {}
    test_vars = [
        "SCREENRENAMER_WATCH_PATH",
        "SCREENRENAMER_LLM_MODEL",
        "SCREENRENAMER_LLM_URL",
        "SCREENRENAMER_LLM_TIMEOUT",
        "SCREENRENAMER_LLM_TEMPERATURE",
        "SCREENRENAMER_SYSTEM_PROMPT",
    ]

    for var in test_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_env.items():
        os.environ[var] = value


@pytest.fixture
def reset_global_config():
    """Reset the global configuration singleton."""
    from screenrenamer.config import _config

    original_config = _config
    _config = None

    yield

    # Restore original config
    _config = original_config


@pytest.fixture
def reset_global_logger():
    """Reset the global logger singleton."""
    from screenrenamer.logger import _logger

    original_logger = _logger
    _logger = None

    yield

    # Restore original logger
    _logger = original_logger
