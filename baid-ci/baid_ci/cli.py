"""Command-line interface for BAID-CI with API key support

This module provides the command-line interface for the BAID-CI tool.
"""

import argparse
import sys
import os
import logging
from typing import List, Optional

from . import __version__
from .auth import Config, ensure_authenticated
from .commands import execute_command, run_ci_analysis, print_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("baid-ci")

# Check if running from compiled binary
COMPILED = getattr(sys, 'frozen', False)

# Message for unauthorized usage attempts
LICENSE_MESSAGE = """
This copy of BAID-CI is not authorized for use on this system.
Please contact support@beskar.tech for licensing information.
"""


def run_with_analysis(config, command: str) -> int:
    """Run the command and analyze any errors"""
    # Run the command
    exit_code, stdout, stderr = execute_command(command)

    # If the command succeeded, exit
    if exit_code == 0:
        return 0

    # Command failed, analyze the error
    print("\nCommand failed with exit code", exit_code)

    # Analyze and show the error
    analysis = run_ci_analysis(command, stdout, stderr, config)
    print_analysis(analysis)
    return exit_code


def print_version() -> None:
    """Print the version information for BAID-CI"""
    print(f"BAID-CI v{__version__}")
    print("Copyright 2025 Beskar AI Technologies")
    print("Licensed for individual use only")
    print("https://baid.dev")


def print_usage() -> None:
    """Print usage information"""
    print("\nUsage:")
    print("  baid-ci run COMMAND")
    print("  baid-ci login [--api-key KEY]")
    print("  baid-ci logout")
    print("  baid-ci version")
    print("\nExamples:")
    print("  baid-ci run \"npm install\"")
    print("  baid-ci run \"pytest tests/\"")
    print("  baid-ci login --api-key YOUR_API_KEY")


def parse_arguments(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BAID-CI: A CI error analyzer tool using BAID.dev AI services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  baid-ci run "npm install"                    Run npm install and analyze any errors
  baid-ci run "pytest tests/"                  Run pytest and analyze any errors
  baid-ci login                                Interactive login with browser authentication
  baid-ci login --api-key YOUR_API_KEY         Non-interactive login with API key
  baid-ci logout                               Log out and remove stored credentials
  baid-ci version                              Show version information
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a command with error analysis")
    run_parser.add_argument("cmd", help="The command to run", nargs="+")

    # Login command
    login_parser = subparsers.add_parser("login", help="Log in to BAID.dev")
    login_parser.add_argument("--api-key", help="API key for non-interactive authentication", required=False)

    # Logout command
    subparsers.add_parser("logout", help="Log out from BAID.dev")

    # Version command
    subparsers.add_parser("version", help="Show version information")

    # Parse arguments
    return parser.parse_args(args)


def check_license() -> bool:
    """Check if this copy of BAID-CI is licensed for use"""
    # This is a placeholder for a real license check implementation
    # In a real implementation, this would validate against a license server
    # or check a local license file with cryptographic validation

    # For this example, we'll always return True
    return True


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI"""
    # Use provided args or system args
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

    # Check license when running from compiled binary
    if COMPILED and not check_license():
        print(LICENSE_MESSAGE)
        return 1

    # Initialize config
    config = Config()

    # Handle commands
    if parsed_args.command == "login":
        # Check if API key is provided
        api_key = parsed_args.api_key
        use_api_key = api_key is not None

        # For API key login, we want to force a new login
        if use_api_key:
            config.reset()

        if ensure_authenticated(config, use_api_key=use_api_key, api_key=api_key):
            print(f"Successfully logged in as {config.user_email}")
            print(f"Authentication type: {'API Key' if config.auth_type == 'api_key' else 'OAuth'}")
        else:
            print("Login failed")
        return 0

    elif parsed_args.command == "logout":
        # Log out by removing config
        config.reset()
        print("Logged out successfully")
        return 0

    elif parsed_args.command == "run":
        # Ensure the user is authenticated
        if not ensure_authenticated(config):
            print("Authentication required. Please run 'baid-ci login' first.")
            return 1

        # Run the command with analysis
        command = " ".join(parsed_args.cmd)
        return run_with_analysis(config, command)

    else:
        # Unknown command
        print(f"Unknown command: {parsed_args.command}")
        print_usage()
        return 1


# Entry point
if __name__ == "__main__":
    sys.exit(main())