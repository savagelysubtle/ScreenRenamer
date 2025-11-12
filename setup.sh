#!/bin/bash

# ScreenRenamer Setup Script for Linux/macOS
# Run with: chmod +x setup.sh && ./setup.sh

set -e

echo -e "\033[1;36mScreenRenamer Setup Script\033[0m"
echo -e "\033[1;36m==========================\033[0m"

# Check if uv is installed
echo -e "\033[1;33mChecking for uv package manager...\033[0m"
if command -v uv &> /dev/null; then
    echo -e "\033[1;32m✓ uv is installed: $(uv --version)\033[0m"
else
    echo -e "\033[1;31m✗ uv is not installed. Installing...\033[0m"
    if command -v pip &> /dev/null; then
        pip install uv
    else
        echo -e "\033[1;31mPlease install uv manually: https://github.com/astral-sh/uv\033[0m"
        exit 1
    fi
fi

# Install Python dependencies
echo -e "\033[1;33mInstalling Python dependencies...\033[0m"
uv sync
echo -e "\033[1;32m✓ Dependencies installed\033[0m"

# Check if Ollama is installed
echo -e "\033[1;33mChecking for Ollama...\033[0m"
if command -v ollama &> /dev/null; then
    echo -e "\033[1;32m✓ Ollama is installed: $(ollama --version)\033[0m"
else
    echo -e "\033[1;31m✗ Ollama is not installed.\033[0m"
    echo -e "\033[1;33mPlease install Ollama from: https://ollama.com/\033[0m"
    echo -e "\033[1;33mThen run: ollama pull llama3.2-vision:11b\033[0m"

    # Try to detect OS and provide installation command
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "\033[1;33mFor Linux, you can try: curl -fsSL https://ollama.com/install.sh | sh\033[0m"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "\033[1;33mFor macOS, download from: https://ollama.com/download\033[0m"
    fi

    read -p "Would you like to continue without Ollama? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Try to pull the vision model
if command -v ollama &> /dev/null; then
    echo -e "\033[1;33mChecking for llama3.2-vision model...\033[0m"
    if ollama list | grep -q "llama3.2-vision"; then
        echo -e "\033[1;32m✓ llama3.2-vision model is available\033[0m"
    else
        echo -e "\033[1;33mPulling llama3.2-vision:11b model (this may take a while)...\033[0m"
        if ollama pull llama3.2-vision:11b; then
            echo -e "\033[1;32m✓ Model downloaded successfully\033[0m"
        else
            echo -e "\033[1;31m✗ Failed to download model\033[0m"
        fi
    fi
fi

# Test the setup
echo -e "\033[1;33mTesting setup...\033[0m"
if uv run screenrenamer test 2>/dev/null; then
    echo -e "\033[1;32m✓ Setup test passed!\033[0m"
else
    echo -e "\033[1;31m✗ Setup test failed (this is expected if Ollama isn't running)\033[0m"
fi

echo
echo -e "\033[1;32mSetup complete!\033[0m"
echo
echo -e "\033[1;36mTo start watching for screenshots:\033[0m"
echo -e "  uv run screenrenamer start"
echo
echo -e "\033[1;36mTo process existing screenshots:\033[0m"
echo -e "  uv run screenrenamer once"
echo
echo -e "\033[1;36mFor help and options:\033[0m"
echo -e "  uv run screenrenamer --help"
