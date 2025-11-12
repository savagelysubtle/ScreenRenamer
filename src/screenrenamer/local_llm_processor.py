"""Local LLM processor using Hugging Face transformers for vision models."""

import time
import warnings
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer

from .config import LLMConfig, get_config
from .logger import get_logger

# Suppress known deprecation warnings at module level
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")


class LLMProcessor:
    """Handles LLM interactions for image analysis using local Hugging Face models."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or get_config().llm
        self.logger = get_logger("local_llm_processor")
        self.model: AutoModel | None = None
        self.tokenizer: AutoTokenizer | None = None
        self._model_loaded = False

    def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded and ready."""
        if self._model_loaded:
            return

        try:
            self.logger.info(f"🔄 Loading model: {self.config.model_name}")

            # Check CUDA availability
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA is not available. This model requires GPU acceleration and cannot run on CPU.")

            device = torch.device("cuda")
            self.logger.info(f"🖥️ Using GPU: {torch.cuda.get_device_name(0)}")
            # Use float16 for GPU efficiency
            torch_dtype = torch.float16

            # Load model and tokenizer
            model_path = Path("@models") / self.config.model_name.replace("/", "_")

            if not model_path.exists():
                raise FileNotFoundError(f"Model not found at {model_path}. Please run setup first.")

            self.logger.debug(f"📁 Loading model from: {model_path}")

            # Load MiniCPM-V model with proper image processor handling
            import warnings

            # Suppress the specific FutureWarning about image_processor_class
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning,
                                       message=".*image_processor_class.*")
                warnings.filterwarnings("ignore", category=UserWarning,
                                       message=".*slow image processor.*")

                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                )
                self.model = AutoModel.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    dtype=torch_dtype,
                    device_map="cuda",  # Force GPU loading
                    low_cpu_mem_usage=True,
                )

            self.logger.info("🚀 Model loaded on GPU")

            self.model.eval()
            self._model_loaded = True
            self.logger.info(f"✅ Model loaded successfully on {device}")

        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
            raise

    def _encode_image(self, image_path: Path) -> Image.Image:
        """Load and prepare image for the model."""
        try:
            image = Image.open(image_path).convert("RGB")
            self.logger.debug(f"📷 Image loaded: {image_path.name} ({image.size})")
            return image
        except Exception as e:
            self.logger.error(f"Failed to load image {image_path}: {e}")
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

        try:
            self.logger.info(f"🔄 Starting local LLM filename generation for: {image_path.name}")
            start_time = time.time()

            # Ensure model is loaded
            self._ensure_model_loaded()

            # Load and prepare image
            self.logger.debug(f"📷 Preparing image: {image_path.name}")
            image = self._encode_image(image_path)

            # Prepare the prompt
            system_prompt = get_config().system_prompt
            question = "Analyze this screenshot and generate a concise, descriptive filename:"

            self.logger.debug(f"📝 System prompt length: {len(system_prompt)} characters")

            # Generate response using MiniCPM-V
            self.logger.info(f"🚀 Running inference with {self.config.model_name}")
            self.logger.debug("🔧 Using temperature-like sampling")

            msgs = [{"role": "user", "content": [question, image]}]

            with torch.no_grad():
                response = self.model.chat(
                    image=None,  # Image is passed in msgs
                    msgs=msgs,
                    tokenizer=self.tokenizer,
                    sampling=True,
                    temperature=self.config.temperature,
                    max_new_tokens=self.config.max_tokens,
                )

            response_time = time.time() - start_time
            self.logger.info(f"📨 Local LLM response received in {response_time:.2f}s")

            # Extract filename from response
            llm_response = response.strip()
            self.logger.debug(f"📥 Raw LLM response ({len(llm_response)} chars): '{llm_response}'")

            if not llm_response:
                raise ValueError("LLM returned empty response")

            # Extract filename from potentially verbose response
            filename = self._extract_filename_from_response(llm_response)
            self.logger.debug(f"🎯 Extracted filename: '{filename}'")

            # Validate the extracted filename
            if not filename or len(filename.strip()) == 0:
                raise ValueError(
                    f"Could not extract valid filename from response: '{llm_response[:100]}...'"
                )

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
            self.logger.info(f"✅ Filename generated: '{filename}' in {total_time:.2f}s")

            self.logger.log_llm_event(
                "filename_generation",
                self.config.model_name,
                True,
                f"'{filename}' for {image_path.name} ({total_time:.2f}s)",
            )

            return filename

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"❌ Local LLM processing failed after {error_time:.2f}s: {e!s}")
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
        filename_match = re.search(r"FILENAME:\s*([^\n\r]+)", response, re.IGNORECASE)
        if filename_match:
            return filename_match.group(1).strip()

        # Look for patterns that indicate the final answer
        # Common patterns: lines that look like filenames (contain underscores, no spaces at start)
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if (
                line
                and "_" in line
                and not line.startswith(
                    ("Okay", "So", "Let", "First", "The", "I need", "Hmm", "First off")
                )
                and re.match(r"^[a-zA-Z0-9_]{3,35}$", line)
            ):
                return line

        # Fallback: take the last line that looks reasonable
        for line in reversed(lines):
            line = line.strip()
            if line and len(line) >= 3 and len(line) <= 35 and "_" in line:
                # Clean up common prefixes
                line = re.sub(r"^(So|Let|The|I|Okay)\s+", "", line, flags=re.IGNORECASE)
                if re.match(r"^[a-zA-Z0-9_]+$", line):
                    return line

        # Last resort: return the entire cleaned response
        return response.strip()

    def test_connection(self) -> bool:
        """Test if the local model is available and working."""

        try:
            self.logger.info("🔍 Testing local LLM model...")
            start_time = time.time()

            # Ensure model is loaded
            self._ensure_model_loaded()

            # Try a simple inference to test the model
            self.logger.debug("🧪 Running test inference...")

            # Create a simple test image (small white square)
            test_image = Image.new("RGB", (64, 64), color="white")

            msgs = [{"role": "user", "content": ["Test image", test_image]}]

            with torch.no_grad():
                response = self.model.chat(
                    image=None,
                    msgs=msgs,
                    tokenizer=self.tokenizer,
                    sampling=True,
                    temperature=0.1,
                    max_new_tokens=50,
                )

            test_time = time.time() - start_time
            self.logger.info(f"✅ Local LLM test successful in {test_time:.2f}s")
            return True

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"❌ Local LLM test failed after {error_time:.2f}s: {e}")
            return False
