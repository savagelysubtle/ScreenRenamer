"""Tests for folder_watcher.py."""

import time
from unittest.mock import MagicMock, patch

import pytest

from screenrenamer.config import WatcherConfig
from screenrenamer.folder_watcher import FolderWatcher, ScreenshotHandler


class TestScreenshotHandler:
    """Test the ScreenshotHandler class."""

    def test_on_created_directory_ignored(self, temp_dir):
        """Test that directory creation events are ignored."""
        callback = MagicMock()
        handler = ScreenshotHandler(callback, ["*.png"])

        # Mock directory event
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = str(temp_dir / "new_dir")

        handler.on_created(mock_event)

        callback.assert_not_called()

    def test_on_created_non_matching_pattern(self, temp_dir):
        """Test that non-matching file patterns are ignored."""
        callback = MagicMock()
        handler = ScreenshotHandler(callback, ["*.png"])

        # Create a non-matching file
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("content")

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(txt_file)

        handler.on_created(mock_event)

        callback.assert_not_called()

    def test_on_created_matching_pattern(self, temp_dir):
        """Test that matching file patterns trigger callback."""
        callback = MagicMock()
        handler = ScreenshotHandler(callback, ["*.png"])

        # Create a matching file
        png_file = temp_dir / "test.png"
        png_file.write_text("fake png content")

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(png_file)

        handler.on_created(mock_event)

        callback.assert_called_once_with(png_file)

    @patch("time.sleep")
    def test_on_created_debounce(self, mock_sleep, temp_dir):
        """Test that events are debounced."""
        callback = MagicMock()
        handler = ScreenshotHandler(callback, ["*.png"])

        png_file = temp_dir / "test.png"
        png_file.write_text("content")

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(png_file)

        handler.on_created(mock_event)

        # Should sleep for debounce time (default 1.0s)
        mock_sleep.assert_called_once_with(1.0)

    def test_on_created_file_becomes_unstable(self, temp_dir):
        """Test handling when file becomes unstable after debounce."""
        callback = MagicMock()
        handler = ScreenshotHandler(callback, ["*.png"])

        png_file = temp_dir / "test.png"
        # Don't create the file, so it won't exist after debounce

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(png_file)

        handler.on_created(mock_event)

        # Callback should not be called for unstable file
        callback.assert_not_called()

    def test_on_created_callback_error(self, temp_dir):
        """Test that callback errors are logged but don't crash."""
        callback = MagicMock(side_effect=Exception("Callback error"))
        handler = ScreenshotHandler(callback, ["*.png"])

        png_file = temp_dir / "test.png"
        png_file.write_text("content")

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(png_file)

        # Should not raise exception
        handler.on_created(mock_event)

        callback.assert_called_once_with(png_file)

    def test_is_file_ready_success(self, sample_image_path):
        """Test successful file readiness check."""
        handler = ScreenshotHandler(MagicMock(), ["*.png"])

        result = handler._is_file_ready(sample_image_path)

        assert result is True

    def test_is_file_ready_file_locked(self, temp_dir):
        """Test file readiness check when file is locked/unreadable."""
        handler = ScreenshotHandler(MagicMock(), ["*.png"])

        # Create file but mock open to fail
        locked_file = temp_dir / "locked.png"
        locked_file.write_text("content")

        with patch("builtins.open", side_effect=OSError("File locked")):
            result = handler._is_file_ready(locked_file)

            assert result is False


class TestFolderWatcher:
    """Test the FolderWatcher class."""

    def test_init_default_config(self, temp_dir, mock_config):
        """Test initialization with default config."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        assert watcher.callback == callback
        assert watcher.config is not None
        assert watcher.observer is None
        assert watcher.handler is None

    def test_init_custom_config(self, temp_dir):
        """Test initialization with custom config."""
        callback = MagicMock()
        custom_config = WatcherConfig(watch_path=temp_dir, patterns=["*.jpg"])
        watcher = FolderWatcher(callback, custom_config)

        assert watcher.config == custom_config

    @patch("screenrenamer.folder_watcher.Observer")
    def test_start_success(self, mock_observer_class, temp_dir):
        """Test successful watcher start."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        mock_observer = MagicMock()
        mock_observer_class.return_value = mock_observer

        watcher.start()

        assert watcher.observer == mock_observer
        assert watcher.handler is not None
        assert watcher.is_running() is True

        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()

    @patch("screenrenamer.folder_watcher.Observer")
    def test_start_already_running(self, mock_observer_class, temp_dir):
        """Test starting when already running."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        # Mock already running
        watcher._running.set()

        watcher.start()

        # Should not create new observer
        mock_observer_class.assert_not_called()

    @patch("screenrenamer.folder_watcher.Observer")
    def test_start_observer_error(self, mock_observer_class, temp_dir):
        """Test handling of observer startup errors."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        mock_observer = MagicMock()
        mock_observer.start.side_effect = Exception("Observer error")
        mock_observer_class.return_value = mock_observer

        with pytest.raises(Exception, match="Observer error"):
            watcher.start()

        assert watcher.is_running() is False

    def test_stop_not_running(self, temp_dir):
        """Test stopping when not running."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        # Should not raise error
        watcher.stop()

        assert watcher.is_running() is False

    @patch("screenrenamer.folder_watcher.Observer")
    def test_stop_success(self, mock_observer_class, temp_dir):
        """Test successful watcher stop."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        mock_observer = MagicMock()
        mock_observer_class.return_value = mock_observer

        watcher.start()
        watcher.stop()

        assert watcher.is_running() is False
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()

    @patch("screenrenamer.folder_watcher.Observer")
    def test_stop_join_timeout(self, mock_observer_class, temp_dir):
        """Test stop when observer doesn't stop gracefully."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        mock_observer = MagicMock()
        mock_observer.is_alive.return_value = True  # Still alive after join
        mock_observer_class.return_value = mock_observer

        watcher.start()
        watcher.stop()

        # Should still be marked as stopped
        assert watcher.is_running() is False

    @patch("screenrenamer.folder_watcher.Observer")
    def test_stop_error(self, mock_observer_class, temp_dir):
        """Test handling of errors during stop."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        mock_observer = MagicMock()
        mock_observer.stop.side_effect = Exception("Stop error")
        mock_observer_class.return_value = mock_observer

        watcher.start()

        # Should not raise exception
        watcher.stop()

        assert watcher.is_running() is False

    def test_is_running(self, temp_dir):
        """Test is_running method."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        assert watcher.is_running() is False

        watcher._running.set()
        assert watcher.is_running() is True

    def test_wait(self, temp_dir):
        """Test wait method."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        # Start watcher in running state
        watcher._running.set()

        # Stop it in a separate "thread" after a short delay
        def stop_after_delay():
            time.sleep(0.1)
            watcher._running.clear()

        import threading

        thread = threading.Thread(target=stop_after_delay)
        thread.start()

        start_time = time.time()
        watcher.wait()
        end_time = time.time()

        # Should have waited at least 0.1 seconds
        assert end_time - start_time >= 0.05  # Allow some tolerance

    def test_context_manager(self, temp_dir):
        """Test context manager functionality."""
        callback = MagicMock()
        watcher = FolderWatcher(callback)

        with (
            patch.object(watcher, "start") as mock_start,
            patch.object(watcher, "stop") as mock_stop,
        ):
            with watcher as w:
                assert w == watcher
                mock_start.assert_called_once()

            mock_stop.assert_called_once()
