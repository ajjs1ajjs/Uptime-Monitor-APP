import sys

sys.path.insert(0, "Uptime_Robot")

import asyncio
from Uptime_Robot import main

# Just try to import and see what happens
print("Imports OK")

# Try to generate HTML
try:
    # Check if we can generate the dashboard HTML
    print("Testing HTML generation...")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
