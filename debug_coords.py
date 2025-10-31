#!/usr/bin/env python3
"""
Debug script to understand coordinate systems
"""

import mss
import Quartz

# Get mss monitors
sct = mss.mss()
monitors = sct.monitors

print("=" * 60)
print("MSS Monitors:")
print("=" * 60)
for i, mon in enumerate(monitors):
    print(f"Monitor {i}: {mon}")

# Get Quartz displays
err, ids, cnt = Quartz.CGGetActiveDisplayList(16, None, None)
if err == Quartz.kCGErrorSuccess:
    print("\n" + "=" * 60)
    print("Quartz Displays:")
    print("=" * 60)
    for i, did in enumerate(ids[:cnt]):
        bounds = Quartz.CGDisplayBounds(did)
        print(f"Display {i}: origin=({bounds.origin.x}, {bounds.origin.y}), size=({bounds.size.width}x{bounds.size.height})")

# Get global bounds
min_x = min_y = float("inf")
max_x = max_y = -float("inf")
for did in ids[:cnt]:
    r = Quartz.CGDisplayBounds(did)
    x0, y0 = r.origin.x, r.origin.y
    x1, y1 = x0 + r.size.width, y0 + r.size.height
    min_x, min_y = min(min_x, x0), min(min_y, y0)
    max_x, max_y = max(max_x, x1), max(max_y, y1)

print("\n" + "=" * 60)
print("Quartz Global Bounds:")
print("=" * 60)
print(f"min_x={min_x}, min_y={min_y}, max_x={max_x}, max_y={max_y}")
print(f"Total width={max_x - min_x}, Total height={max_y - min_y}")

# Get current cursor position
event = Quartz.CGEventCreate(None)
cursor_location = Quartz.CGEventGetLocation(event)

print("\n" + "=" * 60)
print("Current Cursor Position:")
print("=" * 60)
print(f"Quartz (bottom-left origin): x={cursor_location.x}, y={cursor_location.y}")

# Try conversion
screen_y_v1 = max_y - cursor_location.y
print(f"Converted to top-left (using max_y): x={cursor_location.x}, y={screen_y_v1}")

# Adjust for mss offset
combined = monitors[0]
img_x = cursor_location.x - combined['left']
img_y = screen_y_v1 - combined['top']
print(f"Adjusted for mss offset: x={img_x}, y={img_y}")

print("\n" + "=" * 60)
print("Instructions:")
print("=" * 60)
print("Move your cursor to the TOP-LEFT corner of your primary display")
print("and note the coordinates shown above.")
print("Then move to BOTTOM-RIGHT and run again.")

sct.close()

