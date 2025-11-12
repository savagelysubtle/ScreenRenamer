@echo off
REM ScreenRenamer - Quick Start Script
REM This script can be run from anywhere to start ScreenRenamer

echo.
echo ========================================
echo   ScreenRenamer - AI Screenshot Renamer
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Change to the ScreenRenamer directory
cd /d "%SCRIPT_DIR%"

REM Check if .venv exists
if not exist ".venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run 'setup-screenrenamer.bat' first or run 'uv sync' manually.
    echo.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] Configuration file not found!
    echo Running setup first...
    echo.
    uv run screenrenamer setup
    if errorlevel 1 (
        echo [ERROR] Setup failed!
        pause
        exit /b 1
    )
    echo.
)

REM Start ScreenRenamer
echo Starting ScreenRenamer...
echo.
echo Press Ctrl+C to stop watching
echo.

uv run screenrenamer start

REM If it exits, pause so user can see any error messages
if errorlevel 1 (
    echo.
    echo [ERROR] ScreenRenamer exited with an error.
    pause
)

