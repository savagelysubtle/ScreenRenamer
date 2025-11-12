"""Main orchestrator that coordinates all components."""

import time
from pathlib import Path

from .config import ScreenRenamerConfig, get_config, set_config
from .file_renamer import FileRenamer
from .folder_watcher import FolderWatcher
from .llm_processor import LLMProcessor
from .logger import get_logger, setup_logging


class ScreenRenamerOrchestrator:
    """Main orchestrator for the screenshot renaming system."""

    def __init__(self, config: ScreenRenamerConfig | None = None):
        self.logger = get_logger("orchestrator")
        self.logger.info("🛠️ Initializing ScreenRenamer orchestrator...")

        if config:
            set_config(config)
            self.logger.debug("✅ Custom config provided, setting global config")

        self.config = config or get_config()
        self.logger.debug(f"📋 Using configuration: watch_path={self.config.watcher.watch_path}, model={self.config.llm.model_name}")

        # Initialize components
        self.logger.debug("🔧 Setting up logging configuration...")
        setup_logging(self.config.logging)

        self.logger.debug("🤖 Initializing LLM processor...")
        self.llm_processor = LLMProcessor(self.config.llm)

        self.logger.debug("📁 Initializing file renamer...")
        self.file_renamer = FileRenamer(self.config.renamer)

        self.watcher: FolderWatcher | None = None
        self._processed_files = set()  # Track processed files to avoid duplicates

        self.logger.info("✅ ScreenRenamer orchestrator initialized successfully")
        self.logger.debug(f"📊 Initial state: processed_files={len(self._processed_files)}, watcher=None")

    def _process_screenshot(self, file_path: Path) -> None:
        """Process a single screenshot file."""

        start_time = time.time()
        self.logger.info(f"🎯 Starting processing of screenshot: {file_path.name}")

        try:
            # Skip if already processed
            if str(file_path) in self._processed_files:
                self.logger.debug(f"⏭️ Skipping already processed file: {file_path.name}")
                return

            self.logger.debug(f"📁 File path: {file_path}")
            self.logger.debug(f"📊 File size: {file_path.stat().st_size} bytes")
            self.logger.debug(f"📅 File modified: {time.ctime(file_path.stat().st_mtime)}")

            # Generate new filename using LLM
            self.logger.info(f"🤖 Requesting filename generation from LLM for: {file_path.name}")
            llm_start_time = time.time()

            new_name = self.llm_processor.generate_filename(file_path)

            llm_time = time.time() - llm_start_time
            self.logger.debug(f"✅ LLM processing completed in {llm_time:.2f}s")

            # Validate the generated name
            if not new_name or not new_name.strip():
                raise ValueError("LLM returned empty or whitespace-only filename")

            self.logger.debug(f"🏷️ Generated filename: '{new_name}'")

            # Rename the file
            self.logger.info(f"📝 Renaming file: {file_path.name} -> {new_name}{file_path.suffix}")
            rename_start_time = time.time()

            new_path = self.file_renamer.rename_file(file_path, new_name)

            rename_time = time.time() - rename_start_time
            self.logger.debug(f"✅ File rename completed in {rename_time:.2f}s")

            # Mark as processed
            self._processed_files.add(str(new_path))
            self.logger.debug(f"📋 Added to processed files set. Total processed: {len(self._processed_files)}")

            total_time = time.time() - start_time
            self.logger.info(f"🎉 Successfully processed: {file_path.name} -> {new_path.name} (total: {total_time:.2f}s)")

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"❌ Failed to process {file_path.name} after {error_time:.2f}s: {e}")
            self.logger.debug(f"🔍 Error type: {type(e).__name__}")
            self.logger.debug(f"📋 Error details: {e!s}", exc_info=True)
            # Don't re-raise - we want to continue processing other files

    def test_llm_connection(self) -> bool:
        """Test LLM connection and availability."""

        self.logger.info("🔍 Testing LLM connection and model availability...")
        start_time = time.time()

        try:
            result = self.llm_processor.test_connection()
            test_time = time.time() - start_time

            if result:
                self.logger.info(f"✅ LLM connection test passed in {test_time:.2f}s")
            else:
                self.logger.warning(f"⚠️ LLM connection test failed in {test_time:.2f}s")
                self.logger.debug("📋 Check that Ollama is running and the model is downloaded")

            return result

        except Exception as e:
            error_time = time.time() - start_time
            self.logger.error(f"❌ LLM connection test error after {error_time:.2f}s: {e}")
            return False

    def start_watching(self) -> None:
        """Start the folder watching process."""

        start_time = time.time()
        self.logger.info("🚀 Starting ScreenRenamer orchestrator...")

        # Check if already running
        if self.watcher and self.watcher.is_running():
            self.logger.warning("⚠️ Watcher is already running - skipping start")
            return

        self.logger.debug(f"📁 Watch path: {self.config.watcher.watch_path}")
        self.logger.debug(f"🔍 File patterns: {self.config.watcher.patterns}")
        self.logger.debug(f"🔄 Recursive watching: {self.config.watcher.recursive}")
        self.logger.debug(f"⏱️ Debounce seconds: {self.config.watcher.debounce_seconds}")

        # Test LLM connection first
        self.logger.info("🔗 Verifying LLM service availability...")
        if not self.test_llm_connection():
            raise RuntimeError("LLM service is not available. Please ensure Ollama is running and the model is downloaded.")

        # Create and start watcher
        self.logger.debug("👀 Creating folder watcher...")
        self.watcher = FolderWatcher(self._process_screenshot, self.config.watcher)

        self.logger.info("▶️ Starting folder watcher...")
        watcher_start_time = time.time()
        self.watcher.start()
        watcher_startup_time = time.time() - watcher_start_time

        # Verify watcher started successfully
        if self.watcher.is_running():
            total_time = time.time() - start_time
            self.logger.info("✅ ScreenRenamer orchestrator started successfully")
            self.logger.debug(f"⏱️ Total startup time: {total_time:.2f}s (watcher: {watcher_startup_time:.2f}s)")
            self.logger.debug(f"📊 Current state: watching={self.watcher.is_running()}, processed_files={len(self._processed_files)}")
        else:
            raise RuntimeError("Failed to start folder watcher")

    def stop_watching(self) -> None:
        """Stop the folder watching process."""

        start_time = time.time()
        self.logger.info("🛑 Stopping ScreenRenamer orchestrator...")

        if not self.watcher:
            self.logger.debug("ℹ️ No watcher instance found - nothing to stop")
            return

        was_running = self.watcher.is_running()
        self.logger.debug(f"📊 Watcher state before stop: running={was_running}")

        # Stop the watcher
        self.logger.debug("⏹️ Stopping folder watcher...")
        stop_start_time = time.time()
        self.watcher.stop()
        stop_time = time.time() - stop_start_time

        self.logger.debug(f"⏹️ Watcher stop time: {stop_time:.2f}s")

        # Clean up
        self.watcher = None

        total_time = time.time() - start_time
        self.logger.info("✅ ScreenRenamer orchestrator stopped")
        self.logger.debug(f"📊 Final state: watcher=None, processed_files={len(self._processed_files)}")
        self.logger.debug(f"⏱️ Total shutdown time: {total_time:.2f}s")

    def run_once(self) -> None:
        """Process existing files in the watch directory once."""

        start_time = time.time()
        self.logger.info("🔄 Starting batch processing of existing files...")

        if not self.test_llm_connection():
            raise RuntimeError("LLM service is not available. Please ensure Ollama is running and the model is downloaded.")

        watch_path = self.config.watcher.watch_path
        patterns = self.config.watcher.patterns

        self.logger.info(f"📁 Scanning directory: {watch_path}")
        self.logger.debug(f"🔍 Using patterns: {patterns}")

        # Discover all files first
        all_files = []
        for pattern in patterns:
            self.logger.debug(f"🔎 Searching for pattern: {pattern}")
            pattern_files = list(watch_path.glob(pattern))
            self.logger.debug(f"📋 Found {len(pattern_files)} files matching {pattern}")
            all_files.extend(pattern_files)

        # Filter to actual files and remove duplicates
        unique_files = []
        seen_paths = set()
        for file_path in all_files:
            if file_path.is_file() and str(file_path) not in seen_paths:
                unique_files.append(file_path)
                seen_paths.add(str(file_path))

        total_files = len(unique_files)
        self.logger.info(f"📊 Found {total_files} unique files to process")

        if total_files == 0:
            self.logger.info("ℹ No files found to process")
            return

        # Process files with progress tracking
        processed_count = 0
        failed_count = 0
        skipped_count = 0

        for i, file_path in enumerate(unique_files, 1):
            file_start_time = time.time()

            self.logger.info(f"📄 Processing file {i}/{total_files}: {file_path.name}")
            self.logger.debug(f"📂 Full path: {file_path}")

            try:
                # Check if already processed
                if str(file_path) in self._processed_files:
                    self.logger.debug(f"⏭️ Skipping already processed: {file_path.name}")
                    skipped_count += 1
                    continue

                self._process_screenshot(file_path)
                processed_count += 1

                file_time = time.time() - file_start_time
                self.logger.debug(".2f")

                # Small delay to avoid overwhelming the LLM
                if i < total_files:  # Don't delay after the last file
                    self.logger.debug("⏳ Cooling down before next file...")
                    time.sleep(0.5)

            except Exception as e:
                failed_count += 1
                file_time = time.time() - file_start_time
                self.logger.error(f"❌ Failed to process {file_path.name} in {file_time:.2f}s: {e}")

        # Summary
        total_time = time.time() - start_time
        self.logger.info("🎯 Batch processing completed!")
        self.logger.info(f"📊 Summary: {processed_count} processed, {failed_count} failed, {skipped_count} skipped")
        self.logger.debug(f"⏱️ Total processing time: {total_time:.2f}s")
        self.logger.debug(f"📈 Success rate: {(processed_count / max(total_files, 1)) * 100:.1f}%")

    def get_status(self) -> dict:
        """Get current status of the orchestrator."""
        self.logger.debug("📊 Generating status report...")

        # Get watcher status safely
        watching = False
        if self.watcher:
            try:
                watching = self.watcher.is_running()
                self.logger.debug(f"👀 Watcher status: {'running' if watching else 'stopped'}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not get watcher status: {e}")
                watching = False

        # Test LLM connection
        llm_available = self.test_llm_connection()

        status = {
            "watching": watching,
            "watch_path": str(self.config.watcher.watch_path),
            "llm_model": self.config.llm.model_name,
            "llm_available": llm_available,
            "processed_files_count": len(self._processed_files),
            "file_patterns": self.config.watcher.patterns,
        }

        self.logger.debug(f"📈 Status: watching={watching}, llm_available={llm_available}, processed={len(self._processed_files)}")
        return status
