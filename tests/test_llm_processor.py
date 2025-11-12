"""Tests for llm_processor.py."""

import base64
from unittest.mock import MagicMock, patch

import pytest

from screenrenamer.config import LLMConfig
from screenrenamer.local_llm_processor import LLMProcessor


class TestLLMProcessor:
    """Test the LLMProcessor class."""

    def test_init_default_config(self, mock_config):
        """Test initialization with default config."""
        processor = LLMProcessor()

        assert processor.config is not None
        assert isinstance(processor.config, LLMConfig)

    def test_init_custom_config(self, mock_config):
        """Test initialization with custom config."""
        custom_config = LLMConfig(model_name="custom-model")
        processor = LLMProcessor(custom_config)

        assert processor.config == custom_config

    def test_encode_image_success(self, sample_image_path):
        """Test successful image encoding."""
        processor = LLMProcessor()

        result = processor._encode_image(sample_image_path)

        # Should return base64 string
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert decoded.startswith(b"\x89PNG")  # PNG signature

    def test_encode_image_file_not_found(self, temp_dir):
        """Test encoding when image file doesn't exist."""
        processor = LLMProcessor()
        nonexistent_file = temp_dir / "nonexistent.png"

        with pytest.raises(OSError):
            processor._encode_image(nonexistent_file)

    def test_sanitize_filename_basic(self, temp_dir):
        """Test basic filename sanitization."""
        processor = LLMProcessor()

        assert processor._sanitize_filename("valid_name") == "valid_name"
        assert processor._sanitize_filename("test file") == "test file"

    def test_sanitize_filename_unsafe_chars(self, temp_dir):
        """Test sanitization of unsafe characters."""
        processor = LLMProcessor()

        unsafe_name = 'file<>:"/\\|?*name'
        result = processor._sanitize_filename(unsafe_name)

        # Should replace unsafe chars with underscores
        assert '<>:"/\\|?*' not in result
        assert "_" in result

    def test_sanitize_filename_whitespace(self, temp_dir):
        """Test sanitization of leading/trailing whitespace."""
        processor = LLMProcessor()

        assert processor._sanitize_filename("  test  ") == "test"
        assert processor._sanitize_filename(" .test. ") == "test"

    def test_sanitize_filename_multiple_spaces(self, temp_dir):
        """Test sanitization of multiple spaces and underscores."""
        processor = LLMProcessor()

        assert processor._sanitize_filename("test  file") == "test file"
        assert processor._sanitize_filename("test__file") == "test_file"

    def test_sanitize_filename_length_limit(self, temp_dir):
        """Test filename length limiting."""
        processor = LLMProcessor()

        long_name = "a" * 300  # Much longer than limit
        result = processor._sanitize_filename(long_name)

        # Should be truncated (limit is max_filename_length - 10)
        assert len(result) <= 245  # 255 - 10
        assert not result.endswith(" _-")  # Should be cleaned

    def test_generate_filename_success(self, sample_image_path, mock_ollama_client):
        """Test successful filename generation."""
        processor = LLMProcessor()
        processor.client = mock_ollama_client

        result = processor.generate_filename(sample_image_path)

        assert result == "test_filename"
        mock_ollama_client.chat.assert_called_once()

    def test_generate_filename_encoding_failure(self, temp_dir):
        """Test handling of image encoding failure."""
        processor = LLMProcessor()
        nonexistent_file = temp_dir / "nonexistent.png"

        with pytest.raises(OSError):
            processor.generate_filename(nonexistent_file)

    def test_generate_filename_llm_error(self, sample_image_path, mock_ollama_client):
        """Test handling of LLM API errors."""
        processor = LLMProcessor()
        processor.client = mock_ollama_client

        # Mock chat to raise exception
        mock_ollama_client.chat.side_effect = Exception("LLM API error")

        with pytest.raises(Exception, match="LLM API error"):
            processor.generate_filename(sample_image_path)

    def test_generate_filename_invalid_response_format(self, sample_image_path, mock_ollama_client):
        """Test handling of invalid LLM response format."""
        processor = LLMProcessor()
        processor.client = mock_ollama_client

        # Mock response without message key
        mock_response = MagicMock()
        del mock_response.message  # Remove message attribute
        mock_ollama_client.chat.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid response format"):
            processor.generate_filename(sample_image_path)

    def test_generate_filename_empty_response(self, sample_image_path, mock_ollama_client):
        """Test handling of empty LLM response."""
        processor = LLMProcessor()
        processor.client = mock_ollama_client

        # Mock empty response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = ""
        mock_response.message = mock_message
        mock_ollama_client.chat.return_value = mock_response

        with pytest.raises(ValueError, match="LLM returned empty response"):
            processor.generate_filename(sample_image_path)

    def test_generate_filename_whitespace_response(self, sample_image_path, mock_ollama_client):
        """Test handling of whitespace-only LLM response."""
        processor = LLMProcessor()
        processor.client = mock_ollama_client

        # Mock whitespace-only response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "   \n\t   "
        mock_response.message = mock_message
        mock_ollama_client.chat.return_value = mock_response

        with pytest.raises(ValueError, match="LLM returned empty filename after cleaning"):
            processor.generate_filename(sample_image_path)

    def test_generate_filename_with_quotes(self, sample_image_path, mock_ollama_client):
        """Test handling of quoted LLM response."""
        processor = LLMProcessor()
        processor.client = mock_ollama_client

        # Mock response with quotes
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '"quoted_filename"'
        mock_response.message = mock_message
        mock_ollama_client.chat.return_value = mock_response

        result = processor.generate_filename(sample_image_path)

        assert result == "quoted_filename"

    @patch("screenrenamer.llm_processor.ollama.Client")
    def test_test_connection_success(self, mock_client_class, mock_ollama_client):
        """Test successful connection test."""
        mock_client_class.return_value = mock_ollama_client
        processor = LLMProcessor()

        result = processor.test_connection()

        assert result is True
        mock_ollama_client.list.assert_called_once()

    @patch("screenrenamer.llm_processor.ollama.Client")
    def test_test_connection_no_models(self, mock_client_class, mock_ollama_client):
        """Test connection test when no models are available."""
        mock_client_class.return_value = mock_ollama_client

        # Mock empty models list
        mock_models = MagicMock()
        mock_models.models = []
        mock_ollama_client.list.return_value = mock_models

        processor = LLMProcessor()
        result = processor.test_connection()

        assert result is False

    @patch("screenrenamer.llm_processor.ollama.Client")
    def test_test_connection_missing_models_attribute(self, mock_client_class, mock_ollama_client):
        """Test connection test when models attribute is missing."""
        mock_client_class.return_value = mock_ollama_client

        # Mock response without models attribute
        mock_models = MagicMock()
        del mock_models.models
        mock_ollama_client.list.return_value = mock_models

        processor = LLMProcessor()
        result = processor.test_connection()

        assert result is False

    @patch("screenrenamer.llm_processor.ollama.Client")
    def test_test_connection_model_not_found(self, mock_client_class, mock_ollama_client):
        """Test connection test when configured model is not available."""
        mock_client_class.return_value = mock_ollama_client

        # Mock different model in response
        mock_model = MagicMock()
        mock_model.model = "different-model"
        mock_models = MagicMock()
        mock_models.models = [mock_model]
        mock_ollama_client.list.return_value = mock_models

        processor = LLMProcessor(LLMConfig(model_name="test-model"))
        result = processor.test_connection()

        assert result is False

    @patch("screenrenamer.llm_processor.ollama.Client")
    def test_test_connection_api_error(self, mock_client_class, mock_ollama_client):
        """Test connection test when API call fails."""
        mock_client_class.return_value = mock_ollama_client

        # Mock API error
        mock_ollama_client.list.side_effect = Exception("API error")

        processor = LLMProcessor()
        result = processor.test_connection()

        assert result is False
