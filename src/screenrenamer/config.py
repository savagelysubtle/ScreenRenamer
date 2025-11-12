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

    model_name: str = Field(default="openbmb/minicpm-v4.5:8b", description="Ollama model name")
    base_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
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


class ScreenRenamerConfig(BaseModel):
    """Main configuration for ScreenRenamer."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    watcher: WatcherConfig
    renamer: RenamerConfig = Field(default_factory=RenamerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # System prompt for LLM
    system_prompt: str = Field(
        default=(
            "You are an expert at creating perfect filenames for screenshots. "
            "Analyze the image and generate a concise, descriptive filename that captures the essence of what's shown.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "- Return ONLY the filename with no additional text, quotes, or explanation\n"
            "- Do not include any reasoning, thinking, or analysis in your response\n"
            "- Just output the filename directly\n\n"
            "GUIDELINES:\n"
            "- Focus on the PRIMARY activity, application, or content visible\n"
            "- Use 2-4 key words connected by underscores\n"
            "- Be specific: include app names, websites, or activity types\n"
            "- Avoid generic terms like 'screenshot' or 'image'\n"
            "- Keep under 35 characters total\n"
            "- Make it searchable and meaningful\n\n"
            "EXAMPLES:\n"
            "- VS Code editing Python: vscode_python_development\n"
            "- Browser on GitHub: chrome_github_repository\n"
            "- Desktop with multiple apps: desktop_multitasking_view\n"
            "- Game playing: minecraft_survival_world\n"
            "- Terminal commands: terminal_bash_scripting\n"
            "- Document editing: word_resume_formatting\n"
            "- Video call: zoom_team_meeting\n\n"
            "FILENAME:"
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
            model_name=os.getenv("SCREENRENAMER_LLM_MODEL", "llama3.2-vision:11b"),
            base_url=os.getenv("SCREENRENAMER_LLM_URL", "http://localhost:11434"),
            timeout=int(os.getenv("SCREENRENAMER_LLM_TIMEOUT", "120")),
            temperature=float(os.getenv("SCREENRENAMER_LLM_TEMPERATURE", "0.1")),
        )

        return cls(
            llm=llm_config,
            watcher=watcher_config,
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
