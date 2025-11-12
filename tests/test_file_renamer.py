"""Tests for file_renamer.py."""

from unittest.mock import patch

import pytest

from screenrenamer.config import RenamerConfig
from screenrenamer.file_renamer import FileRenamer


class TestFileRenamer:
    """Test the FileRenamer class."""

    def test_init_default_config(self, temp_dir):
        """Test initialization with default config."""
        renamer = FileRenamer()

        assert renamer.config is not None
        assert isinstance(renamer.config, RenamerConfig)

    def test_init_custom_config(self, temp_dir):
        """Test initialization with custom config."""
        custom_config = RenamerConfig(max_filename_length=50, conflict_resolution="skip")
        renamer = FileRenamer(custom_config)

        assert renamer.config == custom_config

    def test_generate_unique_name_no_conflict(self, temp_dir):
        """Test generating unique name when no conflict exists."""
        renamer = FileRenamer()
        directory = temp_dir / "subdir"
        directory.mkdir()

        result = renamer._generate_unique_name(directory, "test", ".png")
        assert result == "test.png"

    def test_generate_unique_name_with_conflicts(self, temp_dir):
        """Test generating unique name with existing files."""
        renamer = FileRenamer()
        directory = temp_dir / "subdir"
        directory.mkdir()

        # Create existing files
        (directory / "test.png").write_text("existing")
        (directory / "test_1.png").write_text("existing")
        (directory / "test_2.png").write_text("existing")

        result = renamer._generate_unique_name(directory, "test", ".png")
        assert result == "test_3.png"

    def test_generate_unique_name_too_many_conflicts(self, temp_dir):
        """Test handling when too many naming conflicts occur."""
        renamer = FileRenamer()

        # Create many conflicting files
        for i in range(1001):
            (temp_dir / f"test_{i}.png").write_text("existing")

        with pytest.raises(ValueError, match="Too many naming conflicts"):
            renamer._generate_unique_name(temp_dir, "test", ".png")

    def test_validate_filename_valid(self, temp_dir):
        """Test filename validation with valid names."""
        renamer = FileRenamer()

        assert renamer._validate_filename("valid_name") == "valid_name"
        assert renamer._validate_filename("test-file_123") == "test-file_123"

    def test_validate_filename_empty(self, temp_dir):
        """Test filename validation with empty name."""
        renamer = FileRenamer()

        with pytest.raises(ValueError, match="Filename cannot be empty"):
            renamer._validate_filename("")

    def test_validate_filename_too_long(self, temp_dir):
        """Test filename validation with name that's too long."""
        renamer = FileRenamer(RenamerConfig(max_filename_length=10))
        long_name = "this_name_is_way_too_long_for_the_limit"

        result = renamer._validate_filename(long_name)
        assert len(result) <= 10
        assert result.endswith("long_for")  # Should be truncated and cleaned

    def test_validate_filename_invalid_after_truncation(self, temp_dir):
        """Test filename validation when truncation leaves only invalid chars."""
        renamer = FileRenamer(RenamerConfig(max_filename_length=5))
        name = "___invalid___"

        with pytest.raises(ValueError, match="results in empty name after cleaning"):
            renamer._validate_filename(name)

    def test_rename_file_basic(self, temp_dir):
        """Test basic file renaming."""
        renamer = FileRenamer()
        source_file = temp_dir / "source.png"
        source_file.write_text("test content")

        result = renamer.rename_file(source_file, "new_name")

        assert result == temp_dir / "new_name.png"
        assert result.exists()
        assert not source_file.exists()
        assert result.read_text() == "test content"

    def test_rename_file_nonexistent_source(self, temp_dir):
        """Test renaming when source file doesn't exist."""
        renamer = FileRenamer()
        nonexistent_file = temp_dir / "nonexistent.png"

        with pytest.raises(FileNotFoundError, match="Source file does not exist"):
            renamer.rename_file(nonexistent_file, "new_name")

    def test_rename_file_conflict_increment(self, temp_dir):
        """Test renaming with increment conflict resolution."""
        renamer = FileRenamer(RenamerConfig(conflict_resolution="increment"))
        source_file = temp_dir / "source.png"
        source_file.write_text("test")

        # Create conflicting file
        (temp_dir / "target.png").write_text("existing")

        result = renamer.rename_file(source_file, "target")

        assert result.name == "target_1.png"
        assert result.exists()
        assert not source_file.exists()

    def test_rename_file_conflict_overwrite(self, temp_dir):
        """Test renaming with overwrite conflict resolution."""
        renamer = FileRenamer(RenamerConfig(conflict_resolution="overwrite"))
        source_file = temp_dir / "source.png"
        source_file.write_text("new content")
        target_file = temp_dir / "target.png"
        target_file.write_text("old content")

        result = renamer.rename_file(source_file, "target")

        assert result == target_file
        assert result.read_text() == "new content"
        assert not source_file.exists()

    def test_rename_file_conflict_skip(self, temp_dir):
        """Test renaming with skip conflict resolution."""
        renamer = FileRenamer(RenamerConfig(conflict_resolution="skip"))
        source_file = temp_dir / "source.png"
        source_file.write_text("test")
        target_file = temp_dir / "target.png"
        target_file.write_text("existing")

        with pytest.raises(FileExistsError, match="Target file already exists"):
            renamer.rename_file(source_file, "target")

        # Source file should still exist
        assert source_file.exists()
        assert target_file.exists()

    def test_rename_file_with_backup(self, temp_dir):
        """Test renaming with backup creation."""
        renamer = FileRenamer(RenamerConfig(backup_original=True))
        source_file = temp_dir / "source.png"
        source_file.write_text("original")

        result = renamer.rename_file(source_file, "new_name")

        assert result.exists()
        assert not source_file.exists()

        # Check backup was created
        backup_file = temp_dir / "source.png.backup"
        assert backup_file.exists()
        assert backup_file.read_text() == "original"

    def test_rename_file_backup_failure(self, temp_dir):
        """Test handling of backup creation failure."""
        renamer = FileRenamer(RenamerConfig(backup_original=True))

        # Create source file
        source_file = temp_dir / "source.png"
        source_file.write_text("content")

        # Mock shutil.copy2 to fail
        with patch("shutil.copy2", side_effect=OSError("Backup failed")):
            # Should still succeed despite backup failure
            result = renamer.rename_file(source_file, "new_name")

            assert result.exists()
            assert not source_file.exists()

    def test_rename_file_os_error(self, temp_dir):
        """Test handling of OS errors during rename."""
        renamer = FileRenamer()
        source_file = temp_dir / "source.png"
        source_file.write_text("content")

        # Mock os.rename to fail
        with patch("os.rename", side_effect=OSError("Rename failed")):
            with pytest.raises(RuntimeError, match="Failed to rename"):
                renamer.rename_file(source_file, "new_name")

            # Source file should still exist
            assert source_file.exists()

    def test_rename_file_backup_restore_on_failure(self, temp_dir):
        """Test that backup is restored when rename fails."""
        renamer = FileRenamer(RenamerConfig(backup_original=True))
        source_file = temp_dir / "source.png"
        source_file.write_text("original")

        # Mock os.rename to fail
        with patch("os.rename", side_effect=OSError("Rename failed")):
            with pytest.raises(RuntimeError):
                renamer.rename_file(source_file, "new_name")

            # Original file should be restored from backup
            assert source_file.exists()
            assert source_file.read_text() == "original"

    def test_rollback_rename_success(self, temp_dir):
        """Test successful rollback operation."""
        renamer = FileRenamer()
        current_file = temp_dir / "current.png"
        current_file.write_text("current content")

        backup_file = temp_dir / "original.png.backup"
        backup_file.write_text("original content")

        result = renamer.rollback_rename(current_file, backup_file)

        assert result is True
        assert not current_file.exists()
        assert (temp_dir / "original.png").exists()
        assert (temp_dir / "original.png").read_text() == "original content"

    def test_rollback_rename_no_backup(self, temp_dir):
        """Test rollback when backup file doesn't exist."""
        renamer = FileRenamer()
        current_file = temp_dir / "current.png"
        current_file.write_text("content")

        nonexistent_backup = temp_dir / "nonexistent.backup"

        result = renamer.rollback_rename(current_file, nonexistent_backup)

        assert result is False
        # Current file should still exist
        assert current_file.exists()

    def test_rollback_rename_os_error(self, temp_dir):
        """Test rollback failure due to OS error."""
        renamer = FileRenamer()
        current_file = temp_dir / "current.png"
        current_file.write_text("current")

        backup_file = temp_dir / "backup.png.backup"
        backup_file.write_text("backup")

        # Mock os.rename to fail
        with patch("os.rename", side_effect=OSError("OS error")):
            result = renamer.rollback_rename(current_file, nonexistent_backup)

            assert result is False
            # Files should remain in original state
            assert current_file.exists()
            assert backup_file.exists()
