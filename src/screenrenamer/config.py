"""Configuration management for ScreenRenamer."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

try:
    from typing import Self
except ImportError:
    from typing import Self

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available, continue with system env vars
    pass

if TYPE_CHECKING:
    pass


class LLMConfig(BaseModel):
    """Configuration for the local LLM."""

    model_name: str = Field(default="openbmb/MiniCPM-V-4_5", description="Hugging Face model name")
    timeout: int = Field(default=120, description="Request timeout in seconds")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(default=200, description="Maximum tokens in response")


class WatcherConfig(BaseModel):
    """Configuration for the folder watcher."""

    watch_path: Path = Field(description="Directory to watch for screenshots")
    patterns: list[str] = Field(
        default=["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff"],
        description="File patterns to monitor",
    )
    recursive: bool = Field(default=False, description="Watch subdirectories recursively")
    debounce_seconds: float = Field(default=1.0, description="Debounce time for file events")


class RenamerConfig(BaseModel):
    """Configuration for file renaming."""

    max_filename_length: int = Field(default=255, description="Maximum filename length")
    safe_characters_only: bool = Field(
        default=True, description="Only allow safe filename characters"
    )
    backup_original: bool = Field(default=True, description="Create backup before renaming")
    conflict_resolution: str = Field(
        default="increment",
        description="How to handle naming conflicts: 'increment', 'overwrite', 'skip'",
    )


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file_path: Path | None = Field(
        default=None, description="Log file path (None for console only)"
    )


class NotificationConfig(BaseModel):
    """Configuration for desktop notifications."""

    enabled: bool = Field(default=True, description="Enable desktop notifications")
    app_name: str = Field(default="ScreenRenamer", description="Application name in notifications")
    show_rename_success: bool = Field(
        default=True, description="Show notification on successful rename"
    )
    show_batch_complete: bool = Field(
        default=True, description="Show notification when batch processing completes"
    )
    show_errors: bool = Field(default=False, description="Show notification on processing errors")


class ScreenRenamerConfig(BaseModel):
    """Main configuration for ScreenRenamer."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    watcher: WatcherConfig
    renamer: RenamerConfig = Field(default_factory=RenamerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)

    # System prompt for LLM
    system_prompt: str = Field(
        default=(
            "You are an expert at creating perfect filenames for screenshots.\n\n"
            "⚠️ CRITICAL OUTPUT FORMAT:\n"
            "- Output ONLY the filename - nothing else\n"
            "- NO explanations, NO thinking, NO quotes, NO punctuation\n"
            "- NO sentences like 'The filename is...' or 'Based on...'\n"
            "- Just the raw filename itself, immediately\n\n"
            "FORMAT RULES:\n"
            "- Use lowercase letters and numbers only\n"
            "- Separate words with underscores: word_word_word\n"
            "- Length: 2-4 words, under 35 characters total\n"
            "- Pattern: [app/context]_[main_content]_[activity]\n\n"
            "CONTENT PRIORITIES (what to include):\n"
            "1. Application name (vscode, chrome, terminal, excel, etc.)\n"
            "2. Primary subject/website/document (github, aws, report, etc.)\n"
            "3. Key action or type (editing, error, settings, dashboard)\n"
            "4. Important context if clear (dark_mode, mobile_view, etc.)\n\n"
            "SPECIFICITY GUIDELINES:\n"
            "✓ DO: Identify specific apps, websites, brands, technologies\n"
            "✓ DO: Capture the main activity or purpose\n"
            "✓ DO: Include error/warning/success states if prominent\n"
            "✗ DON'T: Use vague terms (screen, window, display, image)\n"
            "✗ DON'T: Include date/time (handled automatically)\n"
            "✗ DON'T: Use full sentences or natural language\n\n"
            "EXAMPLES:\n"
            "• VS Code with Python file: vscode_python_editing\n"
            "• Chrome on GitHub repo: chrome_github_repo\n"
            "• Terminal running commands: terminal_command_execution\n"
            "• Excel spreadsheet with charts: excel_chart_analysis\n"
            "• Error dialog box: vscode_error_dialog\n"
            "• Settings page: windows_settings_display\n"
            "• Game screenshot: minecraft_survival_gameplay\n"
            "• Video conference: zoom_meeting_active\n"
            "• Code with error: vscode_python_error\n"
            "• Dashboard with metrics: grafana_metrics_dashboard\n\n"
            "Now analyze the screenshot and output the filename:"
        ),
        description="System prompt for the LLM",
    )

    @model_validator(mode="after")
    def validate_watch_path(self) -> Self:
        """Validate that watch path exists and is a directory."""
        if not self.watcher.watch_path.exists():
            raise ValueError(f"Watch path does not exist: {self.watcher.watch_path}")
        if not self.watcher.watch_path.is_dir():
            raise ValueError(f"Watch path is not a directory: {self.watcher.watch_path}")
        return self

    @classmethod
    def from_env(cls) -> Self:
        """Load configuration from environment variables."""
        # Get watch path from env or use default screenshots directory
        watch_path_str = os.getenv("SCREENRENAMER_WATCH_PATH")
        if not watch_path_str:
            # Default to user's screenshots folder
            if os.name == "nt":  # Windows
                watch_path = Path.home() / "Pictures" / "Screenshots"
            else:  # Unix-like systems
                watch_path = Path.home() / "Pictures" / "Screenshots"
                if not watch_path.exists():
                    watch_path = Path.home()  # fallback to home
        else:
            watch_path = Path(watch_path_str)

        # Create watcher config with the path
        watcher_config = WatcherConfig(watch_path=watch_path)

        # Override other settings from environment
        llm_config = LLMConfig(
            model_name=os.getenv("SCREENRENAMER_LLM_MODEL", "openbmb/MiniCPM-V-4_5"),
            timeout=int(os.getenv("SCREENRENAMER_LLM_TIMEOUT", "120")),
            temperature=float(os.getenv("SCREENRENAMER_LLM_TEMPERATURE", "0.1")),
        )

        # Create notification config from environment
        notification_config = NotificationConfig(
            enabled=os.getenv("SCREENRENAMER_NOTIFICATIONS_ENABLED", "true").lower() == "true",
            show_rename_success=os.getenv("SCREENRENAMER_NOTIFY_SUCCESS", "true").lower() == "true",
            show_batch_complete=os.getenv("SCREENRENAMER_NOTIFY_BATCH", "true").lower() == "true",
            show_errors=os.getenv("SCREENRENAMER_NOTIFY_ERRORS", "false").lower() == "true",
        )

        return cls(
            llm=llm_config,
            watcher=watcher_config,
            notifications=notification_config,
            system_prompt=os.getenv(
                "SCREENRENAMER_SYSTEM_PROMPT", cls.model_fields["system_prompt"].default
            ),
        )


# Global config instance
_config: ScreenRenamerConfig | None = None


def get_config() -> ScreenRenamerConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = ScreenRenamerConfig.from_env()
    return _config


def set_config(config: ScreenRenamerConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
