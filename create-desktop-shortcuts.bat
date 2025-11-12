@echo off
REM Create Desktop Shortcut for ScreenRenamer
REM Run this to create a shortcut on your desktop

echo.
echo ========================================
echo   Creating Desktop Shortcuts
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Create VBS script to generate shortcuts
set "VBS_SCRIPT=%TEMP%\create_shortcuts.vbs"

echo Creating shortcut script...

(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sDesktop = oWS.SpecialFolders^("Desktop"^)
echo.
echo ' Create Start ScreenRenamer shortcut
echo Set oLink = oWS.CreateShortcut^(sDesktop ^& "\Start ScreenRenamer.lnk"^)
echo oLink.TargetPath = "%SCRIPT_DIR%start-screenrenamer.bat"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
echo oLink.Description = "Start ScreenRenamer - AI Screenshot Renamer"
echo oLink.Save
echo.
echo ' Create Setup ScreenRenamer shortcut
echo Set oLink = oWS.CreateShortcut^(sDesktop ^& "\Setup ScreenRenamer.lnk"^)
echo oLink.TargetPath = "%SCRIPT_DIR%setup-screenrenamer.bat"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
echo oLink.Description = "Setup ScreenRenamer"
echo oLink.Save
echo.
echo WScript.Echo "Shortcuts created successfully!"
) > "%VBS_SCRIPT%"

REM Run the VBS script
cscript //nologo "%VBS_SCRIPT%"

REM Clean up
del "%VBS_SCRIPT%"

echo.
echo ========================================
echo   Shortcuts Created!
echo ========================================
echo.
echo Check your desktop for:
echo   - Start ScreenRenamer.lnk
echo   - Setup ScreenRenamer.lnk
echo.
echo You can now double-click these shortcuts from anywhere!
echo.
pause

