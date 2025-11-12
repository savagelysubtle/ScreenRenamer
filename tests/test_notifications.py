#!/usr/bin/env python3
"""Test script for notifications."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from screenrenamer.notifications import NotificationManager

def test_notifications():
    """Test notification functionality."""
    print("=== Testing ScreenRenamer notifications ===")
    print("Starting test...")

    try:
        print("Creating notification manager...")
        # Create notification manager
        nm = NotificationManager(app_name="ScreenRenamer Test", enabled=True)

        print(f"Notification manager enabled: {nm.enabled}")
        print(f"Platform: {nm._get_platform_info()}")

        # Test basic notification
        print("Sending test notification...")
        success = nm.test_notification()
        print(f"Test notification result: {success}")

        # Test file renamed notification
        print("Sending file renamed notification...")
        nm.send_file_renamed_notification("old_screenshot.png", "new_descriptive_name.png")

        # Test batch completion notification
        print("Sending batch completion notification...")
        nm.send_processing_complete_notification(5)

        print("Notification tests completed successfully!")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notifications()
