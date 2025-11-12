# ScreenRenamer

AI-powered screenshot renamer with embedded MiniCPM-V vision model.
Automatically watches a folder for new screenshots and renames them based on
their content using a locally embedded vision-capable language model. No
external dependencies required - model downloads automatically on first setup.

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
- 🚀 **Quick Launch**: Double-click batch files to start from anywhere (Windows)

## Requirements

- **Python**: 3.13+
- **GPU**: NVIDIA GPU with CUDA 12.x support (required for local model)
- **Disk Space**: ~8GB for MiniCPM-V model (downloaded automatically)
- **UV**: For package management (recommended)

## Quick Start (Windows)

### Using Batch Files (Easiest)

1. **First Time Setup**:

   - Double-click `setup-screenrenamer.bat`
   - Follow the prompts to configure your screenshot folder

2. **Start Watching**:

   - Double-click `start-screenrenamer.bat`
   - The app will run in a window you can minimize

3. **Optional - Create Desktop Shortcuts**:

   - Double-click `create-desktop-shortcuts.bat`
   - You'll get shortcuts on your desktop for easy access

4. **Test Connection**:
   - Double-click `test-screenrenamer.bat`
   - Verifies CUDA and model are working

### Manual Installation

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

# Create virtual environment with Python 3.13+
uv venv --python 3.13

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
uv sync
```

### 3. Run Setup

The setup command will automatically:

1. Install CUDA-enabled PyTorch (if not already installed)
2. Configure your screenshot watch folder
3. Download the MiniCPM-V vision model (~8GB, one-time)

```bash
screenrenamer setup
```

The setup process includes:

- **Step 1**: Checks for CUDA PyTorch and installs it if needed
- **Step 2**: Configures your screenshot folder
- **Step 3**: Downloads the vision model from Hugging Face

> **Note**: After running `uv sync`, the setup command will automatically detect
> and replace the CPU-only version of PyTorch with the CUDA-enabled version.

## Quick Start

### First Time Setup

The first run will download the MiniCPM-V model (~8GB) and configure your
screenshot folder. The initial model download takes 5-10 minutes depending on
your internet connection:

```bash
# Download model and configure watch folder
uv run screenrenamer setup
```

The setup will:

- Download MiniCPM-V model from Hugging Face (one-time, ~8GB, 5-10 minutes)
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

# LLM model (default: openbmb/MiniCPM-V-4_5)
export SCREENRENAMER_LLM_MODEL="openbmb/MiniCPM-V-4_5"

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

# Note: Model is fixed to embedded MiniCPM-V-4_5

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

ScreenRenamer uses the **MiniCPM-V-4_5** model, which is automatically
downloaded from Hugging Face on first setup:

- **Model**: `openbmb/MiniCPM-V-4_5` (8B parameters)
- **Storage**: ~8GB disk space
- **Source**: Hugging Face Hub
- **License**: Apache 2.0
- **Capabilities**: Advanced vision-language understanding for image description
  and analysis

The model is downloaded to the `@models/` directory and cached locally for
future use.

## Model Management

ScreenRenamer supports switching between different vision-language models by
simply updating your `.env` file. No code changes required!

### Adding a New Model

1. **Choose a compatible model** from Hugging Face Hub that supports:

   - Vision-language understanding (VLMs)
   - The transformers library
   - Similar API to MiniCPM-V (chat interface with image input)

2. **Download the model manually** (optional - you can let ScreenRenamer
   download it):

   ```bash
   # Install huggingface_hub if needed
   uv add huggingface-hub

   # Download a model (replace 'model-name' with actual model)
   uv run python -c "
   from huggingface_hub import snapshot_download
   snapshot_download('model-name', local_dir='@models/model_name')
   "
   ```

3. **Update your `.env` file**:

   ```bash
   # Change this line to your new model
   SCREENRENAMER_LLM_MODEL=your-model-name
   ```

4. **Test the model**:
   ```bash
   uv run screenrenamer test
   ```

### Supported Model Types

ScreenRenamer works with any Hugging Face model that:

- Has vision capabilities (can process images)
- Uses the transformers `AutoModel` and `AutoTokenizer` interface
- Supports chat-style inference with image inputs

**Examples of compatible models:**

- `openbmb/MiniCPM-V-4_5` (current default - 8B parameters)
- `openbmb/MiniCPM-V-2_6` (smaller 2.6B version)
- Other MiniCPM-V variants
- Compatible LLaVA models
- Other vision-language models with similar APIs

### Model Storage Structure

Models are stored in the `@models/` directory:

```
@models/
├── openbmb_MiniCPM-V-4_5/     # Current default model
│   ├── config.json
│   ├── tokenizer.json
│   ├── model-00001-of-00002.safetensors
│   └── ...
└── your_custom_model/         # Your custom model
    ├── config.json
    └── ...
```

### Automatic Model Detection

When you change `SCREENRENAMER_LLM_MODEL` in your `.env` file:

1. ScreenRenamer checks if the model exists in `@models/`
2. If not found, offers to download it automatically
3. Uses the new model for all screenshot processing

**No restarts required** - just update the `.env` and run your next command!

### Performance Considerations

- **Model Size**: Larger models (8B+) provide better accuracy but require more
  RAM/VRAM
- **Download Time**: Initial downloads take 5-10 minutes for MiniCPM-V (8GB),
  longer for larger models
- **Disk Space**: Models range from 2GB to 20GB+ each
- **GPU Memory**: Ensure your GPU has enough VRAM for the chosen model

### Troubleshooting

**Model not found error:**

```bash
# Check if model directory exists
ls -la @models/

# Re-download if corrupted
rm -rf @models/your-model-name
uv run screenrenamer setup  # Will re-download
```

**Out of memory errors:**

- Try a smaller model variant
- Close other GPU-intensive applications
- Consider CPU-only inference (slower but works)

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

## Advanced Troubleshooting

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
uv run python -c "from screenrenamer.local_llm_processor import LLMProcessor; p = LLMProcessor(); p._ensure_model_loaded()"
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
