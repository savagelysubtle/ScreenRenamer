#!/usr/bin/env python3
"""Test Windows notifications."""

import platform
import subprocess
import tempfile

def test_windows_notification():
    """Test Windows toast notification."""
    print(f"Platform: {platform.system()}")

    if platform.system() != "Windows":
        print("Not on Windows, skipping test")
        return

    # Create a temporary PowerShell script for toast notification
    ps_script = '''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>ScreenRenamer Test</text>
            <text>Windows notifications are working!</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ScreenRenamer").Show($toast)
'''

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
            f.write(ps_script)
            temp_script = f.name

        print("Running PowerShell script...")
        result = subprocess.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-File', temp_script],
            capture_output=True,
            text=True,
            timeout=10
        )

        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")

        # Clean up
        import os
        os.unlink(temp_script)

        if result.returncode == 0:
            print("Windows toast notification sent successfully!")
        else:
            print("Windows toast notification failed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_windows_notification()
