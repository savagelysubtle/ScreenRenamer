#!/usr/bin/env python3
"""Simple plyer test."""

try:
    from plyer import notification
    print('plyer imported successfully')
    notification.notify(title='Test', message='Hello World', timeout=5)
    print('notification sent')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
