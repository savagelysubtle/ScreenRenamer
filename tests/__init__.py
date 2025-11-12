"""Tests for screenrenamer package."""

import os
import tempfile
from pathlib import Path

# Ensure we're using test configuration
os.environ.setdefault("SCREENRENAMER_LLM_MODEL", "test-model")
os.environ.setdefault("SCREENRENAMER_LLM_URL", "http://test:8080")

# Create a temporary directory for tests
TEST_TEMP_DIR = Path(tempfile.mkdtemp(prefix="screenrenamer_test_"))

__all__ = ["TEST_TEMP_DIR"]