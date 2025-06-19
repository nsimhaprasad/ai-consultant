#!/usr/bin/env python3
"""
Main entry point for BAID-Sync
This file serves as an absolute import entry point for Nuitka compilation
"""

from baid_sync.cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())