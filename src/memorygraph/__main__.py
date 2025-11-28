"""
Entry point for running MemoryGraph as a module.

Usage:
    python -m memorygraph
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())