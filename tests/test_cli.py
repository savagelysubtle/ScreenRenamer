"""Tests for cli.py."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from screenrenamer.cli import ScreenRenamerCLI


class TestScreenRenamerCLI:
    """Test the ScreenRenamerCLI class."""

    def test_init(self, temp_dir):
        """Test CLI initialization."""
        cli = ScreenRenamerCLI()

        assert cli.console is not None
        assert cli.orchestrator is None
        assert cli._shutdown_requested is False
        assert cli._shutdown_complete is False

    @patch("screenrenamer.cli.ScreenRenamerConfig.from_env")
    def test_check_configuration_exists_valid(self, mock_from_env, temp_dir):
        """Test configuration check with valid config."""
        mock_config = MagicMock()
        mock_config.watcher.watch_path.exists.return_value = True
        mock_config.watcher.watch_path.is_dir.return_value = True
        mock_from_env.return_value = mock_config

        cli = ScreenRenamerCLI()
        result = cli._check_configuration_exists()

        assert result is True

    @patch("screenrenamer.cli.ScreenRenamerConfig.from_env")
    def test_check_configuration_exists_invalid_path(self, mock_from_env, temp_dir):
        """Test configuration check with invalid path."""
        mock_config = MagicMock()
        mock_config.watcher.watch_path.exists.return_value = False
        mock_from_env.return_value = mock_config

        cli = ScreenRenamerCLI()
        result = cli._check_configuration_exists()

        assert result is False

    @patch("screenrenamer.cli.ScreenRenamerConfig.from_env")
    def test_check_configuration_exists_path_not_dir(self, mock_from_env, temp_dir):
        """Test configuration check when path is not a directory."""
        mock_config = MagicMock()
        mock_config.watcher.watch_path.exists.return_value = True
        mock_config.watcher.watch_path.is_dir.return_value = False
        mock_from_env.return_value = mock_config

        cli = ScreenRenamerCLI()
        result = cli._check_configuration_exists()

        assert result is False

    @patch("screenrenamer.cli.ScreenRenamerConfig.from_env")
    def test_check_configuration_exists_exception(self, mock_from_env, temp_dir):
        """Test configuration check when exception occurs."""
        mock_from_env.side_effect = Exception("Config error")

        cli = ScreenRenamerCLI()
        result = cli._check_configuration_exists()

        assert result is False

    def test_create_env_file_new_file(self, temp_dir):
        """Test creating new .env file."""
        cli = ScreenRenamerCLI()
        env_path = temp_dir / ".env"
        watch_path = "/test/path"

        # Change to temp directory so .env is created there
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            cli._create_env_file(watch_path)
        finally:
            os.chdir(old_cwd)

        assert env_path.exists()
        content = env_path.read_text()
        assert "SCREENRENAMER_WATCH_PATH=/test/path" in content

    def test_create_env_file_existing_file(self, temp_dir):
        """Test updating existing .env file."""
        cli = ScreenRenamerCLI()
        env_path = temp_dir / ".env"

        # Create existing file with other content
        env_path.write_text("# Existing config\nOTHER_VAR=value\n")

        # Change to temp directory so .env is updated there
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            cli._create_env_file("/new/path")
        finally:
            os.chdir(old_cwd)

        content = env_path.read_text()
        assert "SCREENRENAMER_WATCH_PATH=/new/path" in content
        assert "OTHER_VAR=value" in content

    def test_create_env_file_replace_existing_watch_path(self, temp_dir):
        """Test replacing existing watch path in .env file."""
        cli = ScreenRenamerCLI()
        env_path = temp_dir / ".env"

        # Create existing file with watch path
        env_path.write_text("SCREENRENAMER_WATCH_PATH=/old/path\n")

        # Change to temp directory so .env is updated there
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            cli._create_env_file("/new/path")
        finally:
            os.chdir(old_cwd)

        content = env_path.read_text()
        assert "SCREENRENAMER_WATCH_PATH=/new/path" in content
        assert "/old/path" not in content

    def test_create_env_file_write_error(self, temp_dir):
        """Test handling of write errors when creating .env file."""
        cli = ScreenRenamerCLI()

        # Change to temp directory and mock write error
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with patch("pathlib.Path.write_text", side_effect=OSError("Write error")):
                # Should not raise exception
                cli._create_env_file("/test/path")
        finally:
            os.chdir(old_cwd)

    @patch("screenrenamer.cli.Confirm.ask")
    @patch("screenrenamer.cli.Prompt.ask")
    @patch("screenrenamer.cli.Path.mkdir")
    @patch("screenrenamer.cli.Path.exists")
    @patch("screenrenamer.cli.Path.is_dir")
    def test_prompt_for_configuration_create_directory(
        self, mock_is_dir, mock_exists, mock_mkdir, mock_prompt, mock_confirm, temp_dir
    ):
        """Test configuration prompting with directory creation."""
        cli = ScreenRenamerCLI()

        # Mock user inputs
        mock_prompt.return_value = str(temp_dir / "new_screenshots")
        mock_confirm.return_value = True  # Create directory

        # Mock path checks
        mock_exists.return_value = False  # Directory doesn't exist
        mock_is_dir.return_value = False

        with patch("screenrenamer.cli.ScreenRenamerConfig.from_env") as mock_from_env:
            mock_config = MagicMock()
            mock_from_env.return_value = mock_config

            result = cli._prompt_for_configuration()

            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            assert result == mock_config

    @patch("screenrenamer.cli.Confirm.ask")
    @patch("screenrenamer.cli.Prompt.ask")
    @patch("screenrenamer.cli.Path.exists")
    @patch("screenrenamer.cli.Path.is_dir")
    def test_prompt_for_configuration_existing_directory(
        self, mock_is_dir, mock_exists, mock_prompt, mock_confirm, temp_dir
    ):
        """Test configuration prompting with existing directory."""
        cli = ScreenRenamerCLI()

        # Mock user inputs
        mock_prompt.return_value = str(temp_dir)
        mock_confirm.return_value = True  # Save config

        # Mock path checks
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        with patch("screenrenamer.cli.ScreenRenamerConfig.from_env") as mock_from_env:
            mock_config = MagicMock()
            mock_from_env.return_value = mock_config

            result = cli._prompt_for_configuration()

            assert result == mock_config

    @patch("screenrenamer.cli.Confirm.ask")
    @patch("screenrenamer.cli.Prompt.ask")
    def test_prompt_for_configuration_invalid_directory(self, mock_prompt, mock_confirm, temp_dir):
        """Test configuration prompting with invalid directory choice."""
        cli = ScreenRenamerCLI()

        # Mock file instead of directory
        invalid_path = temp_dir / "file.txt"
        invalid_path.write_text("content")

        mock_prompt.return_value = str(invalid_path)
        mock_confirm.side_effect = [False, True]  # Don't create, but save config

        with patch("screenrenamer.cli.ScreenRenamerConfig.from_env") as mock_from_env:
            mock_config = MagicMock()
            mock_from_env.return_value = mock_config

            result = cli._prompt_for_configuration()

            assert result == mock_config

    @patch("screenrenamer.cli.argparse.ArgumentParser.parse_args")
    def test_main_setup_command(self, mock_parse_args, temp_dir):
        """Test main function with setup command."""
        mock_parse_args.return_value = argparse.Namespace(command="setup")

        cli = ScreenRenamerCLI()

        with patch.object(cli, "_cmd_setup") as mock_cmd_setup:
            cli.main()

            mock_cmd_setup.assert_called_once()

    @patch("screenrenamer.cli.argparse.ArgumentParser.parse_args")
    def test_main_start_command(self, mock_parse_args, temp_dir):
        """Test main function with start command."""
        mock_parse_args.return_value = argparse.Namespace(command="start")

        cli = ScreenRenamerCLI()

        with patch.object(cli, "_cmd_start") as mock_cmd_start:
            cli.main()

            mock_cmd_start.assert_called_once()

    @patch("screenrenamer.cli.argparse.ArgumentParser.parse_args")
    def test_main_no_command(self, mock_parse_args, temp_dir):
        """Test main function with no command specified."""
        # Mock args without command attribute
        mock_parse_args.return_value = argparse.Namespace()

        cli = ScreenRenamerCLI()

        with patch.object(cli, "_cmd_start") as mock_cmd_start:
            cli.main()

            # Should default to start command
            mock_cmd_start.assert_called_once()

    @patch("screenrenamer.cli.argparse.ArgumentParser.parse_args")
    def test_main_keyboard_interrupt(self, mock_parse_args, temp_dir):
        """Test main function handling keyboard interrupt."""
        mock_parse_args.return_value = argparse.Namespace(command="setup")

        cli = ScreenRenamerCLI()

        with patch.object(cli, "_cmd_setup", side_effect=KeyboardInterrupt):
            # Should not raise exception
            cli.main()

    @patch("screenrenamer.cli.argparse.ArgumentParser.parse_args")
    def test_main_unexpected_error(self, mock_parse_args, temp_dir):
        """Test main function handling unexpected errors."""
        mock_parse_args.return_value = argparse.Namespace(command="setup")

        cli = ScreenRenamerCLI()

        with patch.object(cli, "_cmd_setup", side_effect=Exception("Unexpected error")):
            with pytest.raises(SystemExit):
                cli.main()
