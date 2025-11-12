# ScreenRenamer

AI-powered screenshot renamer using local LLM vision models. Automatically
watches a folder for new screenshots and renames them based on their content
using a local vision-capable language model.

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
- **Ollama**: For running local LLM models
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

# Install dependencies
uv sync
```

### 3. Install Ollama and Vision Model

```bash
# Install Ollama (download from https://ollama.com/)
# Then pull the vision model
ollama pull openbmb/minicpm-v4.5:8b
```

## Quick Start

### First Time Setup

When you first run ScreenRenamer, you'll be prompted to configure which folder
to watch for screenshots:

```bash
uv run screenrenamer start
```

Or run setup explicitly:

```bash
uv run screenrenamer setup
```

The setup will:

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

# LLM model (default: openbmb/minicpm-v4.5:8b)
export SCREENRENAMER_LLM_MODEL="openbmb/minicpm-v4.5:8b"

# Ollama server URL (default: http://localhost:11434)
export SCREENRENAMER_LLM_URL="http://localhost:11434"

# Request timeout (default: 120)
export SCREENRENAMER_LLM_TIMEOUT="120"

# Temperature for LLM responses (default: 0.1)
export SCREENRENAMER_LLM_TEMPERATURE="0.1"

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

# Use different model
uv run screenrenamer start --model llama3.2-vision:11b

# Enable debug logging
uv run screenrenamer start --log-level DEBUG

# Log to file
uv run screenrenamer start --log-file screenrenamer.log
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Folder Watcher │ -> │   LLM Processor  │ -> │  File Renamer   │
│   (watchdog)    │    │    (Ollama)      │    │  (safe ops)     │
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
- **LLMProcessor**: Handles communication with Ollama vision models
- **FileRenamer**: Safely renames files with conflict resolution and backups
- **Orchestrator**: Coordinates all components and manages application lifecycle
- **Config**: Centralized configuration management
- **Logger**: Structured logging with multiple output formats

## Supported File Types

- PNG (`.png`)
- JPEG/JPG (`.jpg`, `.jpeg`)
- BMP (`.bmp`)
- TIFF (`.tiff`)

## LLM Models

Recommended models with vision capabilities:

- **MiniCPM-V 4.5** (8B) - Recommended, excellent performance and efficiency
- **Llama 3.2 Vision** (11B/90B) - Good alternative
- **CogVLM** - Strong VQA performance
- **GLM-4.5V** - Latest from Z.ai
- **Qwen2-VL** - Versatile vision tasks

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

### LLM Connection Issues

```bash
# Test LLM connection
uv run screenrenamer test

# Check Ollama status
ollama list

# Start Ollama service (if needed)
ollama serve
```

### Permission Errors

Make sure the watch directory is readable/writable:

```bash
# Check permissions
ls -la /path/to/watch/directory

# Fix permissions if needed
chmod 755 /path/to/watch/directory
```

### Model Not Found

```bash
# Pull the model
ollama pull openbmb/minicpm-v4.5:8b

# List available models
ollama list
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

- [ ] Support for additional LLM backends (vLLM, transformers)
- [ ] GUI interface option
- [ ] Batch processing mode
- [ ] Custom naming templates
- [ ] Plugin system for different LLM providers
- [ ] macOS/Windows screenshot integration
