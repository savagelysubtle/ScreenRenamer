"""Safe file renaming utilities for ScreenRenamer."""

import contextlib
import os
import shutil
from pathlib import Path

from .config import RenamerConfig, get_config
from .logger import get_logger


class FileRenamer:
    """Handles safe file renaming operations with conflict resolution and rollback."""

    def __init__(self, config: RenamerConfig | None = None):
        self.config = config or get_config().renamer
        self.logger = get_logger("file_renamer")

    def _generate_unique_name(self, directory: Path, base_name: str, extension: str) -> str:
        """Generate a unique filename by appending numbers if needed."""
        candidate = f"{base_name}{extension}"
        counter = 1

        while (directory / candidate).exists():
            candidate = f"{base_name}_{counter}{extension}"
            counter += 1

            # Safety check to prevent infinite loops
            if counter > 1000:
                raise ValueError(f"Too many naming conflicts for {base_name}{extension}")

        return candidate

    def _validate_filename(self, filename: str) -> str:
        """Validate and clean filename."""
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Remove extension if present (we'll add it back)
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2 and len(name_parts[1]) <= 5:  # Assume short extension is file extension
            name, _ = name_parts
        else:
            name = filename

        # Apply length limit
        if len(name) > self.config.max_filename_length:
            name = name[:self.config.max_filename_length].rstrip(' _-')

        # Ensure we still have a valid name
        if not name.strip(' _-'):
            raise ValueError(f"Filename '{filename}' results in empty name after cleaning")

        return name

    def rename_file(self, file_path: Path, new_name: str) -> Path:
        """
        Safely rename a file with conflict resolution.

        Args:
            file_path: Current file path
            new_name: New filename (without extension)

        Returns:
            New file path after renaming

        Raises:
            Exception: If renaming fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {file_path}")

        try:
            # Get file extension
            extension = file_path.suffix

            # Validate and clean the new name
            clean_name = self._validate_filename(new_name)

            # Handle naming conflicts
            directory = file_path.parent
            if self.config.conflict_resolution == "increment":
                final_name = self._generate_unique_name(directory, clean_name, extension)
            elif self.config.conflict_resolution == "overwrite":
                final_name = f"{clean_name}{extension}"
            elif self.config.conflict_resolution == "skip":
                # Check if target exists
                target_path = directory / f"{clean_name}{extension}"
                if target_path.exists():
                    raise FileExistsError(f"Target file already exists: {target_path}")
                final_name = f"{clean_name}{extension}"
            else:
                raise ValueError(f"Unknown conflict resolution: {self.config.conflict_resolution}")

            # Prepare paths
            new_path = directory / final_name

            # Backup original if requested
            backup_path = None
            if self.config.backup_original:
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                try:
                    shutil.copy2(file_path, backup_path)
                    self.logger.debug(f"Created backup: {backup_path}")
                except OSError as e:
                    self.logger.warning(f"Failed to create backup: {e}")
                    backup_path = None

            # Perform rename
            try:
                os.rename(str(file_path), str(new_path))
                self.logger.log_rename_event(file_path, new_path, True)

                # Clean up backup on success (if we don't want to keep it)
                if backup_path and not self.config.backup_original:
                    with contextlib.suppress(OSError):
                        backup_path.unlink()

                return new_path

            except OSError as e:
                # Restore backup on failure
                if backup_path and backup_path.exists():
                    try:
                        os.rename(str(backup_path), str(file_path))
                        self.logger.info(f"Restored backup after rename failure: {file_path}")
                    except OSError:
                        pass  # Ignore restore failures

                raise RuntimeError(f"Failed to rename {file_path} to {new_path}: {e}") from e

        except Exception as e:
            self.logger.log_rename_event(file_path, Path("FAILED"), False, str(e))
            raise

    def rollback_rename(self, current_path: Path, backup_path: Path) -> bool:
        """
        Rollback a rename operation using backup.

        Args:
            current_path: Current file path
            backup_path: Backup file path

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            # Get original name by removing .backup extension
            original_name = backup_path.stem  # Removes .backup but keeps original extension
            original_path = backup_path.parent / original_name

            # Move current file to a temp location first
            temp_path = current_path.with_suffix(f"{current_path.suffix}.temp")
            os.rename(str(current_path), str(temp_path))

            # Restore backup
            os.rename(str(backup_path), str(original_path))

            # Clean up temp file
            with contextlib.suppress(OSError):
                temp_path.unlink()

            self.logger.info(f"Successfully rolled back rename: {current_path} -> {original_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to rollback rename: {e}")
            return False
