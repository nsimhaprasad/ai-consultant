"""Command-line interface for BAID-Sync

This module provides the command-line interface for the BAID-Sync tool.
"""

import argparse
import sys
import os
import logging
from typing import List, Optional
from pathlib import Path

from . import __version__
from .auth import Config, ensure_authenticated
from .sync import DirectorySync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("baid-sync")


def print_version() -> None:
    """Print the version information for BAID-Sync"""
    print(f"BAID-Sync v{__version__}")
    print("Copyright 2025 Beskar AI Technologies")
    print("Licensed for individual use only")
    print("https://baid.dev")


def print_usage() -> None:
    """Print usage information"""
    print("\nUsage:")
    print("  baid-sync start [DIRECTORY] [--interval MINUTES]")
    print("  baid-sync sync [DIRECTORY]")
    print("  baid-sync login [--api-key KEY]")
    print("  baid-sync logout")
    print("  baid-sync version")
    print("\nExamples:")
    print("  baid-sync start                          # Start syncing current directory every 5 minutes")
    print("  baid-sync start /path/to/project         # Start syncing specific directory")
    print("  baid-sync start --interval 10            # Start syncing every 10 minutes")
    print("  baid-sync sync                           # One-time sync of current directory")
    print("  baid-sync login --api-key YOUR_API_KEY   # Non-interactive login with API key")


def parse_arguments(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BAID-Sync: Directory synchronization tool for Google Cloud Storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  baid-sync start                          Start syncing current directory every 5 minutes
  baid-sync start /path/to/project         Start syncing specific directory
  baid-sync start --interval 10            Start syncing every 10 minutes
  baid-sync sync                           One-time sync of current directory
  baid-sync login                          Interactive login with browser authentication
  baid-sync login --api-key YOUR_API_KEY   Non-interactive login with API key
  baid-sync logout                         Log out and remove stored credentials
  baid-sync version                        Show version information
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Start command (continuous sync)
    start_parser = subparsers.add_parser("start", help="Start continuous directory synchronization")
    start_parser.add_argument("directory", nargs="?", default=".", 
                             help="Directory to sync (default: current directory)")
    start_parser.add_argument("--interval", type=int, default=5, 
                             help="Sync interval in minutes (default: 5)")
    start_parser.add_argument("--ignore", action="append", 
                             help="Additional patterns to ignore (can be used multiple times)")

    # Sync command (one-time sync)
    sync_parser = subparsers.add_parser("sync", help="Perform one-time directory synchronization")
    sync_parser.add_argument("directory", nargs="?", default=".", 
                            help="Directory to sync (default: current directory)")
    sync_parser.add_argument("--ignore", action="append", 
                            help="Additional patterns to ignore (can be used multiple times)")

    # Login command
    login_parser = subparsers.add_parser("login", help="Log in to BAID.dev")
    login_parser.add_argument("--api-key", help="API key for non-interactive authentication", required=False)

    # Logout command
    subparsers.add_parser("logout", help="Log out from BAID.dev")

    # Version command
    subparsers.add_parser("version", help="Show version information")

    return parser.parse_args(args)


def validate_directory(directory_path: str) -> Path:
    """Validate and resolve directory path"""
    path = Path(directory_path).resolve()
    
    if not path.exists():
        print(f"Error: Directory does not exist: {path}")
        sys.exit(1)
    
    if not path.is_dir():
        print(f"Error: Path is not a directory: {path}")
        sys.exit(1)
    
    return path


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI"""
    if args is None:
        args = sys.argv[1:]

    # If no arguments, show help and exit
    if not args:
        print_version()
        print_usage()
        return 0

    # Handle version command without parsing (for simplicity)
    if args[0] == "version":
        print_version()
        return 0

    # Parse other arguments
    parsed_args = parse_arguments(args)

    # Initialize config
    config = Config()

    # Handle commands
    if parsed_args.command == "login":
        api_key = parsed_args.api_key
        use_api_key = api_key is not None

        if use_api_key:
            config.reset()

        if ensure_authenticated(config, use_api_key=use_api_key, api_key=api_key):
            print(f"Successfully logged in as {config.user_email}")
            print(f"Authentication type: {'API Key' if config.auth_type == 'api_key' else 'OAuth'}")
        else:
            print("Login failed")
        return 0

    elif parsed_args.command == "logout":
        config.reset()
        print("Logged out successfully")
        return 0

    elif parsed_args.command in ["start", "sync"]:
        # Ensure the user is authenticated
        if not ensure_authenticated(config):
            print("Authentication required. Please run 'baid-sync login' first.")
            return 1

        # Validate directory
        directory_path = validate_directory(parsed_args.directory)
        
        # Prepare ignore patterns
        ignore_patterns = parsed_args.ignore or []
        
        try:
            # Create sync instance
            sync = DirectorySync(config, str(directory_path), ignore_patterns)
            
            if parsed_args.command == "start":
                # Start continuous sync
                print(f"Starting continuous sync of: {directory_path}")
                print(f"Sync interval: {parsed_args.interval} minutes")
                print(f"User: {config.user_email}")
                sync.start_continuous_sync(parsed_args.interval)
            else:
                # Perform one-time sync
                print(f"Syncing directory: {directory_path}")
                print(f"User: {config.user_email}")
                success = sync.sync_directory()
                if success:
                    print("Sync completed successfully")
                    return 0
                else:
                    print("Sync failed")
                    return 1
        
        except KeyboardInterrupt:
            print("\nSync stopped by user")
            return 0
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return 1

    else:
        print(f"Unknown command: {parsed_args.command}")
        print_usage()
        return 1


# Entry point
if __name__ == "__main__":
    sys.exit(main())