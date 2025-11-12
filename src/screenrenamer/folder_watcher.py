"""Folder watcher using watchdog to monitor for new screenshots."""

import time
from collections.abc import Callable
from pathlib import Path
from threading import Event

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import WatcherConfig, get_config
from .logger import get_logger


class ScreenshotHandler(FileSystemEventHandler):
    """Event handler for screenshot file events."""

    def __init__(self, callback: Callable[[Path], None], patterns: list[str]):
        super().__init__()
        self.callback = callback
        self.patterns = patterns
        self.logger = get_logger("watcher_handler")

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if file matches our patterns
        if any(file_path.match(pattern) for pattern in self.patterns):
            self.logger.log_file_event("created", file_path)

            # Debounce the event to avoid processing incomplete files
            # (Some applications write files gradually)
            time.sleep(get_config().watcher.debounce_seconds)

            # Verify file still exists and is not being written to
            if file_path.exists() and self._is_file_ready(file_path):
                try:
                    self.callback(file_path)
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
            else:
                self.logger.debug(f"Skipping unstable file: {file_path}")

    def _is_file_ready(self, file_path: Path, timeout: float = 2.0) -> bool:
        """Check if a file is ready to be processed (not being written to)."""
        try:
            # Try to open the file for reading
            with open(file_path, 'rb') as f:
                f.read(1)
            return True
        except OSError:
            # File is likely still being written to
            return False


class FolderWatcher:
    """Watches a folder for new screenshot files and triggers processing."""

    def __init__(
        self,
        callback: Callable[[Path], None],
        config: WatcherConfig | None = None
    ):
        self.config = config or get_config().watcher
        self.callback = callback
        self.logger = get_logger("folder_watcher")

        # Watchdog components
        self.observer = None  # type: Observer | None
        self.handler: ScreenshotHandler | None = None

        # Control flags
        self._running = Event()
        self._stop_event = Event()

    def start(self) -> None:
        """Start watching the folder."""
        if self._running.is_set():
            self.logger.warning("Watcher is already running")
            return

        try:
            self.logger.info(f"Starting folder watcher for: {self.config.watch_path}")

            # Create event handler
            self.handler = ScreenshotHandler(self.callback, self.config.patterns)

            # Create observer
            self.observer = Observer()
            self.observer.schedule(
                self.handler,
                str(self.config.watch_path),
                recursive=self.config.recursive
            )

            # Start observer
            self.observer.start()
            self._running.set()
            self._stop_event.clear()

            self.logger.info("Folder watcher started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start folder watcher: {e}")
            raise

    def stop(self) -> None:
        """Stop watching the folder."""
        if not self._running.is_set():
            return

        self.logger.info("Stopping folder watcher...")
        self._stop_event.set()

        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)

                if self.observer.is_alive():
                    self.logger.warning("Observer did not stop gracefully")

            self._running.clear()
            self.logger.info("Folder watcher stopped")

        except Exception as e:
            self.logger.error(f"Error stopping folder watcher: {e}")

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running.is_set()

    def wait(self) -> None:
        """Wait for the watcher to be stopped."""
        while self._running.is_set():
            time.sleep(0.1)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
