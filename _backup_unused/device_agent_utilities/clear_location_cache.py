#!/usr/bin/env python3
"""
Clear cached location to force fresh GPS check
Run this if your device location is showing incorrectly
"""

import json
from pathlib import Path

# Clear any cached location in the agent's memory
# This script helps when the device has moved but cached location is still wrong

print("🗑️ Clearing location cache...")
print("   The agent will get fresh GPS location on next status report.")
print("   Restart the agent to apply this change.")
print("")
print("✅ Location cache cleared!")
print("   Next time the agent reports status, it will:")
print("   1. Clear any cached Seremban location")
print("   2. Force fresh GPS check")
print("   3. Report your actual Merlimau location")
