#!/usr/bin/env python3
"""
Main entry point for BAID-CI
This file serves as an absolute import entry point for Nuitka compilation
"""

# Use absolute imports instead of relative imports
from baid_ci.cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())