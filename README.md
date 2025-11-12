# ScreenRenamer

AI-powered screenshot renamer with embedded MiniCPM-V vision model. Automatically
watches a folder for new screenshots and renames them based on their content
using a locally embedded vision-capable language model. No external dependencies
required - model downloads automatically on first setup.

## Features

- 🖼️ **Vision Analysis**: Uses local LLM with vision capabilities to analyze
  screenshot content
- 👀 **Auto-Detection**: Monitors folders for new screenshot files in real-time
- 🏷️ **Smart Naming**: Generates descriptive, concise filenames based on image
  content
- 🛡️ **Safe Operations**: Includes backup and rollback capabilities for failed
  renames
- ⚙️ **Configurable**: Highly customizable through environment variables and CLI
  options
- 📊 **Rich CLI**: Beautiful terminal interface with status monitoring

## Requirements

- **Python**: 3.14+
- **Disk Space**: ~8GB for MiniCPM-V model (downloaded automatically)
- **UV**: For package management (recommended)

## Installation

### 1. Install UV (Package Manager)

```bash
# On Windows (PowerShell)
winget install --id astral-sh.uv

# Or using pip
pip install uv
```

### 2. Clone and Install

```bash
git clone https://github.com/yourusername/screenrenamer.git
cd screenrenamer

# Install dependencies (includes transformers, torch, etc.)
uv sync
```

### 3. First Time Setup

The first time you run ScreenRenamer, it will automatically download the MiniCPM-V model (~8GB) from Hugging Face:

```bash
# This will download the model and set up your watch folder
uv run screenrenamer setup
```

## Quick Start

### First Time Setup

The first run will download the MiniCPM-V model (~8GB) and configure your screenshot folder:

```bash
# Download model and configure watch folder
uv run screenrenamer setup
```

The setup will:

- Download MiniCPM-V model from Hugging Face (one-time, ~8GB)
- Show common screenshot locations
- Let you enter a custom path
- Create the directory if it doesn't exist
- Save your configuration to a `.env` file for future use

### Start Watching

Once configured, start watching for new screenshots:

```bash
# Start watching the configured folder
uv run screenrenamer start
```

### Process Files

Process one specific photo interactively:

```bash
uv run screenrenamer once
```

Process all existing screenshots in the watch folder:

```bash
uv run screenrenamer all
```

### Test LLM Connection

```bash
# Verify everything is set up correctly
uv run screenrenamer test
```

## Configuration

### Environment Variables

```bash
# Watch directory (default: ~/Pictures/Screenshots)
export SCREENRENAMER_WATCH_PATH="/path/to/screenshots"

# LLM model (default: openbmb/MiniCPM-V-2_6)
export SCREENRENAMER_LLM_MODEL="openbmb/MiniCPM-V-2_6"

# Request timeout (default: 120)
export SCREENRENAMER_LLM_TIMEOUT="120"

# Temperature for LLM responses (default: 0.1)
export SCREENRENAMER_LLM_TEMPERATURE="0.1"

# Maximum tokens for LLM responses (default: 100)
export SCREENRENAMER_LLM_MAX_TOKENS="100"

# Custom system prompt
export SCREENRENAMER_SYSTEM_PROMPT="Your custom prompt here"
```

### CLI Options

```bash
# Configure screenshot folder (first time setup)
uv run screenrenamer setup

# Start watching (after setup)
uv run screenrenamer start

# Process one specific photo interactively
uv run screenrenamer once

# Process all photos in watch folder
uv run screenrenamer all

# Specify custom watch path (overrides config)
uv run screenrenamer start --watch-path ./my-screenshots

# Note: Model is fixed to embedded MiniCPM-V-2_6

# Enable debug logging
uv run screenrenamer start --log-level DEBUG

# Log to file
uv run screenrenamer start --log-file screenrenamer.log
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Folder Watcher │ -> │   LLM Processor  │ -> │  File Renamer   │
│   (watchdog)    │    │ (MiniCPM-V local)│    │  (safe ops)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────────────┐
                    │   Orchestrator     │
                    │  (coordinates all) │
                    └────────────────────┘
```

### Components

- **FolderWatcher**: Monitors filesystem for new screenshot files using watchdog
- **LLMProcessor**: Handles local inference with embedded MiniCPM-V model
- **FileRenamer**: Safely renames files with conflict resolution and backups
- **Orchestrator**: Coordinates all components and manages application lifecycle
- **Config**: Centralized configuration management
- **Logger**: Structured logging with multiple output formats
- **ModelManager**: Downloads and manages the MiniCPM-V model from Hugging Face

## Supported File Types

- PNG (`.png`)
- JPEG/JPG (`.jpg`, `.jpeg`)
- BMP (`.bmp`)
- TIFF (`.tiff`)

## LLM Model

ScreenRenamer uses the **MiniCPM-V-2_6** model, which is automatically downloaded from Hugging Face on first setup:

- **Model**: `openbmb/MiniCPM-V-2_6` (2.6B parameters)
- **Storage**: ~8GB disk space
- **Source**: Hugging Face Hub
- **License**: Apache 2.0
- **Capabilities**: Strong vision-language understanding for image description and analysis

The model is downloaded to the `@models/` directory and cached locally for future use.

## Safety Features

- **File Backups**: Original files are backed up before renaming
- **Conflict Resolution**: Handles duplicate names with configurable strategies
- **Rollback**: Can restore from backups if renaming fails
- **Debouncing**: Waits for files to be fully written before processing
- **Error Isolation**: Individual file failures don't stop the watcher

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linter
uv run ruff check

# Run type checker
uv run ty check

# Format code
uv run ruff format
```

### Project Structure

```
src/screenrenamer/
├── __init__.py          # Package initialization
├── cli.py              # Command-line interface
├── config.py           # Configuration management
├── orchestrator.py     # Main application coordinator
├── folder_watcher.py   # Filesystem monitoring
├── llm_processor.py    # LLM integration
├── file_renamer.py     # Safe file operations
└── logger.py           # Logging utilities

tests/                  # Test files
pyproject.toml         # Project configuration
README.md             # This file
```

## Troubleshooting

### Model Download Issues

```bash
# Test LLM connection and model loading
uv run screenrenamer test

# Re-download model if corrupted
uv run screenrenamer setup --force-redownload

# Check model exists in @models/ directory
ls -la @models/
```

### Permission Errors

Make sure the watch directory is readable/writable:

```bash
# Check permissions
ls -la /path/to/watch/directory

# Fix permissions if needed
chmod 755 /path/to/watch/directory
```

### Insufficient Disk Space

The MiniCPM-V model requires ~8GB of free disk space:

```bash
# Check available disk space
df -h

# Clean up if needed
# Remove downloaded model to re-download
rm -rf @models/
```

### Model Loading Errors

If the model fails to load:

```bash
# Check Python version (requires 3.14+)
python --version

# Reinstall dependencies
uv sync --reinstall

# Test model loading specifically
uv run python -c "from screenrenamer.local_llm_processor import LocalLLMProcessor; p = LocalLLMProcessor(); p._ensure_model_loaded()"
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest`
5. Run linter: `uv run ruff check`
6. Submit a pull request

## Roadmap

- [x] Embed MiniCPM-V model locally (no Ollama dependency)
- [ ] GUI interface option
- [ ] Batch processing mode
- [ ] Custom naming templates
- [ ] Support for additional embedded vision models
- [ ] macOS/Windows screenshot integration
- [ ] Model optimization (quantization, smaller variants)
