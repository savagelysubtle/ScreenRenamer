"""LLM processor for analyzing screenshots and generating filenames."""

import base64
from pathlib import Path

import ollama

from .config import LLMConfig, get_config
from .logger import get_logger


class LLMProcessor:
    """Handles LLM interactions for image analysis and filename generation."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or get_config().llm
        self.logger = get_logger("llm_processor")
        self.client = ollama.Client(host=self.config.base_url, timeout=self.config.timeout)

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 for LLM processing."""
        try:
            with open(image_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode("utf-8")
            self.logger.debug(f"Encoded image: {image_path.name} ({len(encoded)} chars)")
            return encoded
        except OSError as e:
            self.logger.error(f"Failed to encode image {image_path}: {e}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be safe for filesystem."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, "_")

        # Remove leading/trailing whitespace and dots
        filename = filename.strip(" .")

        # Replace multiple spaces/underscores with single
        while "  " in filename:
            filename = filename.replace("  ", " ")
        while "__" in filename:
            filename = filename.replace("__", "_")

        # Limit length
        max_length = get_config().renamer.max_filename_length - 10  # Leave room for extension
        if len(filename) > max_length:
            filename = filename[:max_length].rstrip(" _-")

        return filename

    def generate_filename(self, image_path: Path) -> str:
        """
        Analyze an image and generate a descriptive filename.

        Args:
            image_path: Path to the image file

        Returns:
            A sanitized filename without extension

        Raises:
            Exception: If LLM processing fails
        """
        import time

        try:
            self.logger.info(f"🔄 Starting LLM filename generation for: {image_path.name}")
            start_time = time.time()

            # Encode image
            self.logger.debug(f"📷 Encoding image: {image_path.name}")
            encode_start = time.time()
            image_data = self._encode_image(image_path)
            encode_time = time.time() - encode_start
            self.logger.debug(f"✅ Image encoded in {encode_time:.2f}s")

            # Prepare messages using Ollama vision format
            system_prompt = get_config().system_prompt
            self.logger.debug(f"📝 System prompt length: {len(system_prompt)} characters")

            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Analyze this screenshot and generate a concise, descriptive filename:",
                    "images": [image_data],
                },
            ]

            # Call LLM
            self.logger.info(f"🚀 Sending request to {self.config.model_name} for {image_path.name}")
            self.logger.debug(f"🔧 Using temperature: {self.config.temperature}, max_tokens: {self.config.max_tokens}")
            request_start = time.time()

            self.logger.debug("⏳ Waiting for LLM response...")
            response = self.client.chat(
                model=self.config.model_name,
                messages=messages,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            )

            response_time = time.time() - request_start
            self.logger.info(f"📨 LLM response received in {response_time:.2f}s")

            # Extract filename from response
            if "message" not in response:
                raise ValueError(f"Invalid response format: missing 'message' key. Response keys: {list(response.keys())}")

            llm_response = response["message"]["content"].strip()
            self.logger.debug(f"📥 Raw LLM response ({len(llm_response)} chars): '{llm_response}'")

            if not llm_response:
                raise ValueError("LLM returned empty response")

            # Extract filename from potentially verbose response
            filename = self._extract_filename_from_response(llm_response)
            self.logger.debug(f"🎯 Extracted filename: '{filename}'")

            # Validate the extracted filename
            if not filename or len(filename.strip()) == 0:
                raise ValueError(f"Could not extract valid filename from response: '{llm_response[:100]}...'")

            # Clean up the response (remove quotes, extra whitespace)
            filename = filename.strip("\"'").strip()
            self.logger.debug(f"🧹 Cleaned response: '{filename}'")

            # Sanitize for filesystem safety
            filename = self._sanitize_filename(filename)
            self.logger.debug(f"🛡️ Sanitized filename: '{filename}'")

            # Ensure we have a valid filename
            if not filename:
                raise ValueError("LLM returned empty filename after cleaning")

            total_time = time.time() - start_time
            self.logger.info(".2f")
            self.logger.log_llm_event(
                "filename_generation",
                self.config.model_name,
                True,
                f"'{filename}' for {image_path.name} ({total_time:.2f}s)",
            )

            return filename

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"❌ LLM processing failed after {error_time:.2f}s: {e!s}")
            self.logger.log_llm_event(
                "filename_generation",
                self.config.model_name,
                False,
                f"Failed for {image_path.name} after {error_time:.2f}s: {e!s}",
            )
            raise

    def _extract_filename_from_response(self, response: str) -> str:
        """Extract filename from potentially verbose LLM response."""
        import re

        # First, try to find filename after "FILENAME:" marker (from our prompt)
        filename_match = re.search(r'FILENAME:\s*([^\n\r]+)', response, re.IGNORECASE)
        if filename_match:
            return filename_match.group(1).strip()

        # Look for patterns that indicate the final answer
        # Common patterns: lines that look like filenames (contain underscores, no spaces at start)
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if (line and '_' in line and not line.startswith(('Okay', 'So', 'Let', 'First', 'The', 'I need', 'Hmm', 'First off'))
                and re.match(r'^[a-zA-Z0-9_]{3,35}$', line)):
                return line

        # Fallback: take the last line that looks reasonable
        for line in reversed(lines):
            line = line.strip()
            if line and len(line) >= 3 and len(line) <= 35 and '_' in line:
                # Clean up common prefixes
                line = re.sub(r'^(So|Let|The|I|Okay)\s+', '', line, flags=re.IGNORECASE)
                if re.match(r'^[a-zA-Z0-9_]+$', line):
                    return line

        # Last resort: return the entire cleaned response
        return response.strip()

    def test_connection(self) -> bool:
        """Test if the LLM service is available."""
        import time

        try:
            self.logger.info("🔍 Testing LLM connection...")
            start_time = time.time()

            # Try to list models to test connection
            self.logger.debug("📋 Requesting model list from Ollama...")
            list_start = time.time()
            models = self.client.list()
            list_time = time.time() - list_start
            self.logger.debug(f"📋 Model list retrieved in {list_time:.2f}s")

            if not hasattr(models, 'models') or not models.models:
                self.logger.error("❌ No models found in Ollama response")
                return False

            available_models = [model.model for model in models.models]
            self.logger.debug(f"📋 Available models: {available_models}")

            if self.config.model_name not in available_models:
                self.logger.warning(
                    f"❌ Model {self.config.model_name} not found. Available: {available_models}"
                )
                return False

            connection_time = time.time() - start_time
            self.logger.info(f"✅ LLM connection successful in {connection_time:.2f}s")
            return True

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"❌ LLM connection failed after {error_time:.2f}s: {e}")
            return False
