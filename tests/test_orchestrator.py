"""Tests for orchestrator.py."""

from unittest.mock import MagicMock, patch

from screenrenamer.orchestrator import ScreenRenamerOrchestrator


class TestScreenRenamerOrchestrator:
    """Test the ScreenRenamerOrchestrator class."""

    def test_init_default_config(self, temp_dir, mock_config, reset_global_config):
        """Test initialization with default config."""
        orchestrator = ScreenRenamerOrchestrator()

        assert orchestrator.config is not None
        assert orchestrator.llm_processor is not None
        assert orchestrator.file_renamer is not None
        assert orchestrator.watcher is None
        assert len(orchestrator._processed_files) == 0

    def test_init_custom_config(self, temp_dir, mock_config, reset_global_config):
        """Test initialization with custom config."""
        custom_config = mock_config
        orchestrator = ScreenRenamerOrchestrator(custom_config)

        assert orchestrator.config == custom_config

    @patch("screenrenamer.orchestrator.setup_logging")
    def test_init_logging_setup(self, mock_setup_logging, temp_dir, mock_config, reset_global_config):
        """Test that logging is set up during initialization."""
        ScreenRenamerOrchestrator()

        mock_setup_logging.assert_called_once()

    def test_process_screenshot_success(self, temp_dir, mock_config, reset_global_config):
        """Test successful screenshot processing."""
        # Create test image
        image_file = temp_dir / "test.png"
        image_file.write_text("fake image content")

        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Mock LLM processor
        orchestrator.llm_processor.generate_filename = MagicMock(return_value="new_filename")

        # Mock file renamer
        mock_new_path = temp_dir / "new_filename.png"
        orchestrator.file_renamer.rename_file = MagicMock(return_value=mock_new_path)

        orchestrator._process_screenshot(image_file)

        # Check that LLM was called
        orchestrator.llm_processor.generate_filename.assert_called_once_with(image_file)

        # Check that renamer was called
        orchestrator.file_renamer.rename_file.assert_called_once_with(image_file, "new_filename")

        # Check that file was added to processed set
        assert str(mock_new_path) in orchestrator._processed_files

    def test_process_screenshot_already_processed(self, temp_dir, mock_config, reset_global_config):
        """Test processing of already processed file."""
        image_file = temp_dir / "test.png"
        image_file.write_text("content")

        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Mark file as already processed
        orchestrator._processed_files.add(str(image_file))

        # Mock processors (should not be called)
        orchestrator.llm_processor.generate_filename = MagicMock()
        orchestrator.file_renamer.rename_file = MagicMock()

        orchestrator._process_screenshot(image_file)

        # Should not call processors
        orchestrator.llm_processor.generate_filename.assert_not_called()
        orchestrator.file_renamer.rename_file.assert_not_called()

    def test_process_screenshot_llm_failure(self, temp_dir, mock_config, reset_global_config):
        """Test handling of LLM processing failure."""
        image_file = temp_dir / "test.png"
        image_file.write_text("content")

        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Mock LLM to fail
        orchestrator.llm_processor.generate_filename = MagicMock(
            side_effect=Exception("LLM error")
        )

        # Should not raise exception
        orchestrator._process_screenshot(image_file)

        # File should not be added to processed set
        assert str(image_file) not in orchestrator._processed_files

    def test_process_screenshot_invalid_filename(self, temp_dir, mock_config, reset_global_config):
        """Test handling of invalid filename from LLM."""
        image_file = temp_dir / "test.png"
        image_file.write_text("content")

        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Mock LLM to return empty filename
        orchestrator.llm_processor.generate_filename = MagicMock(return_value="")

        # Should not raise exception
        orchestrator._process_screenshot(image_file)

        # File should not be added to processed set
        assert str(image_file) not in orchestrator._processed_files

    def test_process_screenshot_rename_failure(self, temp_dir, mock_config, reset_global_config):
        """Test handling of file rename failure."""
        image_file = temp_dir / "test.png"
        image_file.write_text("content")

        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Mock successful LLM
        orchestrator.llm_processor.generate_filename = MagicMock(return_value="new_name")

        # Mock failed rename
        orchestrator.file_renamer.rename_file = MagicMock(
            side_effect=Exception("Rename failed")
        )

        # Should not raise exception
        orchestrator._process_screenshot(image_file)

        # File should not be added to processed set
        assert str(image_file) not in orchestrator._processed_files

    @patch("screenrenamer.orchestrator.ScreenRenamerOrchestrator._process_screenshot")
    def test_start_watching(self, mock_process, temp_dir, mock_config, reset_global_config):
        """Test starting the file watcher."""
        orchestrator = ScreenRenamerOrchestrator(mock_config)

        with patch("screenrenamer.orchestrator.FolderWatcher") as mock_watcher_class:
            mock_watcher = MagicMock()
            mock_watcher_class.return_value = mock_watcher

            orchestrator.start_watching()

            assert orchestrator.watcher == mock_watcher
            mock_watcher_class.assert_called_once()
            mock_watcher.start.assert_called_once()

    @patch("screenrenamer.orchestrator.ScreenRenamerOrchestrator._process_screenshot")
    def test_stop_watching(self, mock_process, temp_dir, mock_config, reset_global_config):
        """Test stopping the file watcher."""
        orchestrator = ScreenRenamerOrchestrator(mock_config)

        with patch("screenrenamer.orchestrator.FolderWatcher") as mock_watcher_class:
            mock_watcher = MagicMock()
            mock_watcher_class.return_value = mock_watcher

            orchestrator.start_watching()
            orchestrator.stop_watching()

            mock_watcher.stop.assert_called_once()

    def test_test_llm_connection_success(self, temp_dir, mock_config, reset_global_config):
        """Test successful LLM connection test."""
        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Mock successful connection test
        orchestrator.llm_processor.test_connection = MagicMock(return_value=True)

        result = orchestrator.test_llm_connection()

        assert result is True
        orchestrator.llm_processor.test_connection.assert_called_once()

    def test_test_llm_connection_failure(self, temp_dir, mock_config, reset_global_config):
        """Test failed LLM connection test."""
        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Mock failed connection test
        orchestrator.llm_processor.test_connection = MagicMock(return_value=False)

        result = orchestrator.test_llm_connection()

        assert result is False
        orchestrator.llm_processor.test_connection.assert_called_once()

    def test_context_manager(self, temp_dir, mock_config, reset_global_config):
        """Test context manager functionality."""
        orchestrator = ScreenRenamerOrchestrator(mock_config)

        with patch.object(orchestrator, 'start_watching') as mock_start, \
             patch.object(orchestrator, 'stop_watching') as mock_stop:

            with orchestrator as orch:
                assert orch == orchestrator
                mock_start.assert_called_once()

            mock_stop.assert_called_once()

    def test_get_stats(self, temp_dir, mock_config, reset_global_config):
        """Test getting orchestrator statistics."""
        orchestrator = ScreenRenamerOrchestrator(mock_config)

        # Add some processed files
        orchestrator._processed_files.add("file1.png")
        orchestrator._processed_files.add("file2.png")

        stats = orchestrator.get_stats()

        assert stats["processed_files"] == 2
        assert "config" in stats
        assert "llm_available" in stats

    @patch("screenrenamer.orchestrator.ScreenRenamerOrchestrator.test_llm_connection")
    def test_get_stats_llm_status(self, mock_test_connection, temp_dir, mock_config, reset_global_config):
        """Test LLM status in statistics."""
        orchestrator = ScreenRenamerOrchestrator(mock_config)

        mock_test_connection.return_value = True
        stats = orchestrator.get_stats()
        assert stats["llm_available"] is True

        mock_test_connection.return_value = False
        stats = orchestrator.get_stats()
        assert stats["llm_available"] is False
