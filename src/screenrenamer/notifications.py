"""Cross-platform notification system for ScreenRenamer."""

import platform
from pathlib import Path
from typing import Optional

from .logger import get_logger

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class NotificationManager:
    """Manages cross-platform desktop notifications."""

    def __init__(self, app_name: str = "ScreenRenamer", enabled: bool = True):
        self.app_name = app_name
        self.enabled = enabled
        self.logger = get_logger("notifications")

        if not PLYER_AVAILABLE:
            self.logger.debug("plyer not available - using platform-specific fallbacks")
        else:
            self.logger.debug("Notification system initialized with plyer")

    def _get_platform_info(self) -> str:
        """Get platform information for logging."""
        system = platform.system()
        if system == "Windows":
            version = platform.version()
            return f"Windows {version}"
        elif system == "Darwin":
            version = platform.mac_ver()[0]
            return f"macOS {version}"
        elif system == "Linux":
            try:
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=", 1)[1].strip().strip('"')
            except (FileNotFoundError, IOError):
                pass
            return "Linux"
        else:
            return system

    def send_file_renamed_notification(
        self,
        old_filename: str,
        new_filename: str,
        folder_path: Optional[Path] = None
    ) -> None:
        """Send notification for successful file rename."""
        if not self.enabled:
            return

        try:
            title = "Screenshot Renamed"
            message = f"{old_filename} → {new_filename}"

            if folder_path:
                message += f"\n📁 {folder_path.name}"

            self._send_notification(title, message)

        except Exception as e:
            self.logger.debug(f"Failed to send rename notification: {e}")

    def send_processing_complete_notification(
        self,
        file_count: int,
        folder_path: Optional[Path] = None
    ) -> None:
        """Send notification for batch processing completion."""
        if not self.enabled:
            return

        try:
            if file_count == 1:
                title = "Processing Complete"
                message = "1 screenshot processed successfully"
            else:
                title = "Batch Processing Complete"
                message = f"{file_count} screenshots processed successfully"

            if folder_path:
                message += f"\n📁 {folder_path.name}"

            self._send_notification(title, message)

        except Exception as e:
            self.logger.debug(f"Failed to send completion notification: {e}")

    def send_error_notification(self, error_message: str) -> None:
        """Send notification for processing errors."""
        if not self.enabled:
            return

        try:
            title = "Processing Error"
            message = f"Error: {error_message[:100]}..." if len(error_message) > 100 else error_message

            self._send_notification(title, message)

        except Exception as e:
            self.logger.debug(f"Failed to send error notification: {e}")

    def _send_notification(self, title: str, message: str) -> None:
        """Send notification using plyer or platform-specific fallbacks."""
        system = platform.system()

        # On Windows, try Windows-specific toast notifications first
        if system == "Windows":
            try:
                self._windows_fallback(title, message)
                self.logger.debug(f"Windows notification sent: {title}")
                return
            except Exception as e:
                self.logger.debug(f"Windows fallback failed: {e}")

        # Try plyer for other platforms or as fallback
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=5,  # seconds
            )
            self.logger.debug(f"plyer notification sent: {title}")
            return

        except Exception as e:
            self.logger.debug(f"plyer notification failed: {e}")
            # Try fallback methods for specific platforms
            self._fallback_notification(title, message)

    def _fallback_notification(self, title: str, message: str) -> None:
        """Fallback notification methods for when plyer fails."""
        system = platform.system()

        try:
            if system == "Windows":
                self._windows_fallback(title, message)
            elif system == "Darwin":  # macOS
                self._macos_fallback(title, message)
            elif system == "Linux":
                self._linux_fallback(title, message)
        except Exception as e:
            self.logger.debug(f"Fallback notification also failed: {e}")

    def _windows_fallback(self, title: str, message: str) -> None:
        """Windows fallback using toast notifications."""
        try:
            # Try to use Windows built-in notifications
            import subprocess
            import tempfile

            # Create a temporary PowerShell script
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

            $template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{message}</text>
        </binding>
    </visual>
</toast>
"@

            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ScreenRenamer").Show($toast)
            '''

            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
                f.write(ps_script)
                temp_script = f.name

            # Run PowerShell script
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-File', temp_script],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Clean up
            Path(temp_script).unlink(missing_ok=True)

            if result.returncode == 0:
                self.logger.debug("Windows fallback notification sent")
            else:
                self.logger.debug(f"Windows fallback failed: {result.stderr}")

        except Exception as e:
            self.logger.debug(f"Windows fallback notification failed: {e}")

    def _macos_fallback(self, title: str, message: str) -> None:
        """macOS fallback using osascript."""
        try:
            import subprocess

            # Escape quotes in title and message
            safe_title = title.replace('"', '\\"')
            safe_message = message.replace('"', '\\"')

            script = f'display notification "{safe_message}" with title "{safe_title}"'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self.logger.debug("macOS fallback notification sent")
            else:
                self.logger.debug(f"macOS fallback failed: {result.stderr}")

        except Exception as e:
            self.logger.debug(f"macOS fallback notification failed: {e}")

    def _linux_fallback(self, title: str, message: str) -> None:
        """Linux fallback using notify-send."""
        try:
            import subprocess

            result = subprocess.run(
                ['notify-send', title, message],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self.logger.debug("Linux fallback notification sent")
            else:
                self.logger.debug(f"Linux fallback failed: {result.stderr}")

        except Exception as e:
            self.logger.debug(f"Linux fallback notification failed: {e}")

    def test_notification(self) -> bool:
        """Test if notifications are working."""
        if not self.enabled:
            return False

        try:
            self._send_notification("ScreenRenamer", "Notifications are working!")
            return True
        except Exception as e:
            self.logger.debug(f"Notification test failed: {e}")
            return False
