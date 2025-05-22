#!/usr/bin/env python
"""
Script to generate git information files for the application.
This script is used during development and CI/CD to create files with git information.
"""

import os
import subprocess
from pathlib import Path


def get_git_commit_sha():
    """Get the current git commit SHA."""
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        ).strip()
        return git_sha
    except (subprocess.SubprocessError, FileNotFoundError):
        return "unknown"


def main():
    """Generate git information files."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Create the git_info directory if it doesn't exist
    git_info_dir = project_root / "baid_server" / "git_info"
    git_info_dir.mkdir(exist_ok=True)

    # Get the git commit SHA
    git_sha = get_git_commit_sha()

    # Write the git commit SHA to a file
    commit_sha_file = git_info_dir / "commit_sha.txt"
    with open(commit_sha_file, "w") as f:
        f.write(git_sha)

    print(f"Git commit SHA written to {commit_sha_file}: {git_sha}")


if __name__ == "__main__":
    main()
