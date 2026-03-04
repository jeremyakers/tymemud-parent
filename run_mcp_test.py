#!/usr/bin/env python3
"""Standalone test MCP server - runs on stdio like normal but for testing."""

import asyncio
import sys

# Add llm_gateway to path
sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

# Import and run the server
from server import main

if __name__ == "__main__":
    asyncio.run(main())
