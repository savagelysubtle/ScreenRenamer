@echo off
REM ScreenRenamer - Setup Script
REM Run this once to configure ScreenRenamer

echo.
echo ========================================
echo   ScreenRenamer - Setup
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Change to the ScreenRenamer directory
cd /d "%SCRIPT_DIR%"

echo Step 1: Installing/Updating dependencies...
echo.
uv sync
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo Step 2: Running ScreenRenamer setup...
echo.
uv run screenrenamer setup

if errorlevel 1 (
    echo.
    echo [ERROR] Setup failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo You can now run 'start-screenrenamer.bat' to start watching for screenshots.
echo.
pause

