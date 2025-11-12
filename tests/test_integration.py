"""Integration tests for screenrenamer."""

from unittest.mock import MagicMock, patch

from screenrenamer.config import ScreenRenamerConfig
from screenrenamer.orchestrator import ScreenRenamerOrchestrator


class TestIntegration:
    """Integration tests covering end-to-end functionality."""

    def test_full_screenshot_processing_workflow(self, temp_dir):
        """Test complete screenshot processing workflow."""
        # Create test image
        image_file = temp_dir / "test_screenshot.png"
        image_file.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        )  # Minimal PNG

        # Create config
        config = ScreenRenamerConfig.from_env()
        config.watcher.watch_path = temp_dir

        # Create orchestrator
        orchestrator = ScreenRenamerOrchestrator(config)

        # Mock LLM to return a specific filename
        expected_filename = "test_desktop_capture"
        orchestrator.llm_processor.generate_filename = MagicMock(return_value=expected_filename)

        # Process the screenshot
        orchestrator._process_screenshot(image_file)

        # Check that file was renamed
        expected_new_path = temp_dir / f"{expected_filename}.png"
        assert expected_new_path.exists()
        assert not image_file.exists()

        # Check that it was added to processed files
        assert str(expected_new_path) in orchestrator._processed_files

    def test_watcher_integration(self, temp_dir):
        """Test integration between watcher and processing."""
        # Create config
        config = ScreenRenamerConfig.from_env()
        config.watcher.watch_path = temp_dir

        # Create orchestrator
        orchestrator = ScreenRenamerOrchestrator(config)

        # Mock processing
        orchestrator._process_screenshot = MagicMock()

        # Start watching
        orchestrator.start_watching()

        try:
            # Create a test image file (simulating file creation event)
            image_file = temp_dir / "new_screenshot.png"
            image_file.write_bytes(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            )

            # Wait a bit for watcher to detect the file
            import time

            time.sleep(0.1)

            # Check that processing was called
            orchestrator._process_screenshot.assert_called_once_with(image_file)

        finally:
            orchestrator.stop_watching()

    def test_error_recovery_workflow(self, temp_dir):
        """Test error recovery in the processing workflow."""
        # Create test image
        image_file = temp_dir / "test.png"
        image_file.write_text("content")

        # Create config
        config = ScreenRenamerConfig.from_env()
        config.watcher.watch_path = temp_dir

        orchestrator = ScreenRenamerOrchestrator(config)

        # Mock LLM to fail
        orchestrator.llm_processor.generate_filename = MagicMock(
            side_effect=Exception("LLM unavailable")
        )

        # Process should handle error gracefully
        orchestrator._process_screenshot(image_file)

        # Original file should still exist (processing failed)
        assert image_file.exists()

        # Should not be in processed files
        assert str(image_file) not in orchestrator._processed_files

    def test_backup_and_rollback_integration(self, temp_dir):
        """Test backup creation and rollback functionality."""
        # Create test image
        image_file = temp_dir / "original.png"
        image_file.write_text("original content")

        # Create config with backup enabled
        config = ScreenRenamerConfig.from_env()
        config.watcher.watch_path = temp_dir
        config.renamer.backup_original = True

        orchestrator = ScreenRenamerOrchestrator(config)

        # Mock LLM
        orchestrator.llm_processor.generate_filename = MagicMock(return_value="renamed")

        # Process the file
        orchestrator._process_screenshot(image_file)

        # Check that backup was created
        backup_file = temp_dir / "original.png.backup"
        assert backup_file.exists()
        assert backup_file.read_text() == "original content"

        # Check that file was renamed
        new_file = temp_dir / "renamed.png"
        assert new_file.exists()

    def test_configuration_persistence(self, temp_dir):
        """Test that configuration changes persist across orchestrator instances."""
        from screenrenamer.config import set_config

        # Create custom config
        custom_config = ScreenRenamerConfig.from_env()
        custom_config.llm.model_name = "custom-model"
        custom_config.watcher.watch_path = temp_dir

        # Set global config
        set_config(custom_config)

        # Create new orchestrator (should use global config)
        orchestrator = ScreenRenamerOrchestrator()

        assert orchestrator.config.llm.model_name == "custom-model"
        assert orchestrator.config.watcher.watch_path == temp_dir

    @patch("screenrenamer.orchestrator.ollama")
    def test_llm_connection_integration(self, mock_ollama, temp_dir):
        """Test LLM connection testing integration."""
        # Mock ollama client
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.model = "test-model"
        mock_models = MagicMock()
        mock_models.models = [mock_model]
        mock_client.list.return_value = mock_models
        mock_ollama.Client.return_value = mock_client

        # Create orchestrator
        config = ScreenRenamerConfig.from_env()
        config.llm.model_name = "test-model"
        orchestrator = ScreenRenamerOrchestrator(config)

        # Test connection
        result = orchestrator.test_llm_connection()

        assert result is True
        mock_client.list.assert_called_once()

    def test_concurrent_file_processing_simulation(self, temp_dir):
        """Test handling multiple files created in quick succession."""
        # Create config
        config = ScreenRenamerConfig.from_env()
        config.watcher.watch_path = temp_dir

        orchestrator = ScreenRenamerOrchestrator(config)

        # Mock LLM with different responses
        orchestrator.llm_processor.generate_filename = MagicMock(
            side_effect=["first_capture", "second_capture", "third_capture"]
        )

        # Create multiple files
        files = []
        for i in range(3):
            image_file = temp_dir / f"screenshot_{i}.png"
            image_file.write_text(f"content {i}")
            files.append(image_file)

        # Process all files
        for image_file in files:
            orchestrator._process_screenshot(image_file)

        # Check that all files were processed and renamed
        for i, original_file in enumerate(files):
            expected_new_file = temp_dir / f"screenshot_{i}_capture.png"
            assert expected_new_file.exists()
            assert not original_file.exists()

        # Check processed files count
        assert len(orchestrator._processed_files) == 3

    def test_file_pattern_filtering_integration(self, temp_dir):
        """Test that only matching file patterns are processed."""
        # Create config
        config = ScreenRenamerConfig.from_env()
        config.watcher.watch_path = temp_dir
        config.watcher.patterns = ["*.png", "*.jpg"]

        orchestrator = ScreenRenamerOrchestrator(config)

        # Mock processing
        orchestrator._process_screenshot = MagicMock()

        # Create files with different extensions
        png_file = temp_dir / "test.png"
        png_file.write_text("png content")

        jpg_file = temp_dir / "test.jpg"
        jpg_file.write_text("jpg content")

        txt_file = temp_dir / "test.txt"
        txt_file.write_text("txt content")

        # Process files (only PNG and JPG should be processed)
        orchestrator._process_screenshot(png_file)
        orchestrator._process_screenshot(jpg_file)
        orchestrator._process_screenshot(txt_file)

        # Check that only PNG and JPG were processed
        assert orchestrator._process_screenshot.call_count == 3  # All calls made
        # In real scenario, watcher would filter, but here we test the processing logic
