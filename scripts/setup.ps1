# ScreenRenamer Setup Script for Windows
# Run this script to set up the development environment

Write-Host "ScreenRenamer Setup Script" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Check if uv is installed
Write-Host "Checking for uv package manager..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>$null
    Write-Host "✓ uv is installed: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ uv is not installed. Installing..." -ForegroundColor Red
    winget install --id astral-sh.uv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install uv. Please install it manually from https://github.com/astral-sh/uv" -ForegroundColor Red
        exit 1
    }
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
uv sync
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Check if Ollama is installed
Write-Host "Checking for Ollama..." -ForegroundColor Yellow
try {
    $ollamaVersion = ollama --version 2>$null
    Write-Host "✓ Ollama is installed: $ollamaVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Ollama is not installed." -ForegroundColor Red
    Write-Host "Please download and install Ollama from: https://ollama.com/" -ForegroundColor Yellow
    Write-Host "Then run: ollama pull llama3.2-vision:11b" -ForegroundColor Yellow
    $installOllama = Read-Host "Would you like to open the Ollama download page? (y/n)"
    if ($installOllama -eq "y") {
        Start-Process "https://ollama.com/"
    }
}

# Try to pull the vision model
Write-Host "Checking for llama3.2-vision model..." -ForegroundColor Yellow
try {
    $models = ollama list 2>$null
    if ($models -match "llama3.2-vision") {
        Write-Host "✓ llama3.2-vision model is available" -ForegroundColor Green
    } else {
        Write-Host "Pulling llama3.2-vision:11b model (this may take a while)..." -ForegroundColor Yellow
        ollama pull llama3.2-vision:11b
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Model downloaded successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to download model" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "✗ Could not check Ollama models. Make sure Ollama is running." -ForegroundColor Red
}

# Test the setup
Write-Host "Testing setup..." -ForegroundColor Yellow
try {
    uv run screenrenamer test
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Setup test passed!" -ForegroundColor Green
    } else {
        Write-Host "✗ Setup test failed" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Could not run test" -ForegroundColor Red
}

Write-Host "" -ForegroundColor White
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "To start watching for screenshots:" -ForegroundColor Cyan
Write-Host "  uv run screenrenamer start" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "To process existing screenshots:" -ForegroundColor Cyan
Write-Host "  uv run screenrenamer once" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "For help and options:" -ForegroundColor Cyan
Write-Host "  uv run screenrenamer --help" -ForegroundColor White
