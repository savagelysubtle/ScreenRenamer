"""Model management for downloading and managing Hugging Face models."""

import os
from pathlib import Path

from huggingface_hub import snapshot_download
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TransferSpeedColumn,
)

from .logger import get_logger


class ModelManager:
    """Manages downloading and checking for local Hugging Face models."""

    def __init__(self):
        self.logger = get_logger("model_manager")
        self.console = Console()
        self.models_dir = Path("@models")
        self.models_dir.mkdir(exist_ok=True)

    def check_model_exists(self, model_name: str) -> bool:
        """
        Check if a model exists locally.

        Args:
            model_name: Hugging Face model name (e.g., "openbmb/MiniCPM-V-4_5")

        Returns:
            True if model exists locally, False otherwise
        """
        model_path = self.models_dir / model_name.replace("/", "_")
        exists = model_path.exists() and model_path.is_dir()

        if exists:
            # Quick check that it's not empty
            try:
                contents = list(model_path.iterdir())
                exists = len(contents) > 0
            except (OSError, PermissionError):
                exists = False

        self.logger.debug(f"Model {model_name} exists at {model_path}: {exists}")
        return exists

    def download_model_from_huggingface(self, model_name: str, force: bool = False) -> Path:
        """
        Download a model from Hugging Face Hub.

        Args:
            model_name: Hugging Face model name (e.g., "openbmb/MiniCPM-V-4_5")
            force: If True, re-download even if model exists

        Returns:
            Path to the downloaded model directory

        Raises:
            Exception: If download fails
        """
        model_path = self.models_dir / model_name.replace("/", "_")

        # Check if model already exists
        if not force and self.check_model_exists(model_name):
            self.logger.info(f"Model {model_name} already exists at {model_path}")
            self.console.print(f"[green]✓ Model {model_name} already downloaded[/green]")
            return model_path

        try:
            self.logger.info(f"Starting download of {model_name} to {model_path}")
            self.console.print(f"[cyan]📥 Downloading model: {model_name}[/cyan]")
            self.console.print(f"[dim]Destination: {model_path}[/dim]")
            self.console.print(
                "[dim]This may take several minutes depending on your internet connection...[/dim]"
            )
            self.console.print()

            # Set up progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=self.console,
                refresh_per_second=2,
            ) as progress:
                task = progress.add_task(f"Downloading {model_name}...", total=None)

                # Custom progress callback
                def progress_callback(current: int, total: int):
                    if total and total > 0:
                        progress.update(task, completed=current, total=total)
                    else:
                        # For indeterminate progress, just show activity
                        progress.update(
                            task, description=f"Downloading {model_name}... ({current} bytes)"
                        )

                # Download the model
                downloaded_path = snapshot_download(
                    repo_id=model_name,
                    local_dir=model_path,
                    token=os.getenv("HF_TOKEN"),  # Use token if available for gated models
                    # progress_callback=progress_callback,  # huggingface_hub doesn't support this directly
                )

                # Since we can't get progress from snapshot_download, show completion
                progress.update(
                    task, completed=100, total=100, description=f"✅ Downloaded {model_name}"
                )

            self.logger.info(f"Successfully downloaded {model_name} to {downloaded_path}")

            # Verify the download
            if not self.check_model_exists(model_name):
                raise RuntimeError(
                    f"Download completed but model verification failed for {model_name}"
                )

            self.console.print()
            self.console.print("[green]✅ Model downloaded successfully![/green]")
            self.console.print(f"[dim]Location: {model_path}[/dim]")

            return Path(downloaded_path)

        except Exception as e:
            error_msg = f"Failed to download model {model_name}: {e}"
            self.logger.error(error_msg)
            self.console.print(f"[red]❌ {error_msg}[/red]")

            # Clean up partial download if it exists
            if model_path.exists():
                try:
                    import shutil

                    shutil.rmtree(model_path)
                    self.logger.info(f"Cleaned up partial download at {model_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to clean up partial download: {cleanup_error}")

            raise

    def get_model_path(self, model_name: str) -> Path:
        """
        Get the local path for a model.

        Args:
            model_name: Hugging Face model name

        Returns:
            Path to the model directory
        """
        return self.models_dir / model_name.replace("/", "_")

    def cleanup_old_models(self, keep_models: list[str] | None = None) -> None:
        """
        Clean up old/unused models to free disk space.

        Args:
            keep_models: List of model names to keep. If None, keeps all current models.
        """
        if keep_models is None:
            # If no specific models to keep, don't delete anything
            return

        keep_paths = {self.get_model_path(model) for model in keep_models}

        try:
            for model_dir in self.models_dir.iterdir():
                if model_dir.is_dir() and model_dir not in keep_paths:
                    self.logger.info(f"Removing old model directory: {model_dir}")
                    import shutil

                    shutil.rmtree(model_dir)
                    self.console.print(f"[dim]🗑️ Removed old model: {model_dir.name}[/dim]")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old models: {e}")


def download_minicpm_v_model(force: bool = False) -> Path:
    """
    Convenience function to download the default MiniCPM-V model.

    Args:
        force: Force re-download even if model exists

    Returns:
        Path to the downloaded model
    """
    manager = ModelManager()
    return manager.download_model_from_huggingface("openbmb/MiniCPM-V-4_5", force=force)


def check_minicpm_v_model() -> bool:
    """
    Check if the default MiniCPM-V model exists locally.

    Returns:
        True if model exists, False otherwise
    """
    manager = ModelManager()
    return manager.check_model_exists("openbmb/MiniCPM-V-4_5")
