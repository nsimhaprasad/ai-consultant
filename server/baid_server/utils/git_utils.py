"""
Git utilities for the application.
"""
import os
import subprocess
from typing import Optional
from pathlib import Path


def get_git_commit_sha() -> Optional[str]:
    """
    Get the current git commit SHA.

    Returns:
        The git commit SHA as a string, or None if not in a git repository or if there was an error.
    """
    # First, try to read from the file created during Docker build
    commit_sha_file = Path(__file__).parent.parent / "git_info" / "commit_sha.txt"
    if commit_sha_file.exists():
        try:
            with open(commit_sha_file, "r") as f:
                git_sha = f.read().strip()
                if git_sha and git_sha != "unknown":
                    return git_sha
        except Exception:
            pass  # Fall back to other methods

    # Next, try to get it from environment variable (useful in CI/CD environments)
    git_sha = os.environ.get("GIT_COMMIT_SHA")
    if git_sha:
        return git_sha

    # Finally, try to get the git commit SHA using git command
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        ).strip()
        return git_sha
    except (subprocess.SubprocessError, FileNotFoundError):
        return "unknown"
