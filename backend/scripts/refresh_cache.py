#!/usr/bin/env python3
"""Manual cache refresh script.

Run this to manually trigger a full indicator cache refresh without
waiting for the scheduled daily task.

Usage:
    python scripts/refresh_cache.py
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from ecpm.tasks.cache_tasks import run_precompute_sync

if __name__ == "__main__":
    print("=" * 60)
    print("ECPM Indicator Cache Refresh")
    print("=" * 60)
    print()
    print("Starting pre-computation of all indicators...")
    print("This may take several minutes.")
    print()

    try:
        results = run_precompute_sync()

        print()
        print("=" * 60)
        print("Cache refresh completed successfully!")
        print("=" * 60)
        print()
        print("Results:")
        for methodology, count in results.items():
            print(f"  {methodology}: {count} items cached")
        print()

    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR: Cache refresh failed!")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
