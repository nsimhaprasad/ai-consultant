#!/usr/bin/env python3
"""
Script to obfuscate the BAID-CI package using PyArmor
This creates a secure, obfuscated package that can be distributed
without exposing the source code.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_pyarmor():
    """Check if PyArmor is installed and available"""
    try:
        subprocess.run(['pyarmor', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: PyArmor is not installed. Please install it with:")
        print("pip install pyarmor")
        return False


def clean_dist():
    """Clean the dist directory before building"""
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    os.makedirs("dist", exist_ok=True)


def obfuscate_package():
    """Obfuscate the BAID-CI package using PyArmor"""
    print("Obfuscating BAID-CI package...")

    # Run PyArmor to obfuscate the package
    result = subprocess.run([
        'pyarmor', 'obfuscate',
        '--restrict', '3',  # Restrict mode 3 - advanced protection
        '--advanced', '2',  # Advanced obfuscation
        '--bootstrap', '2',  # Bootstrap code protection
        '--output', 'dist/obfuscated',
        'baid_ci/__init__.py'
    ], check=True, capture_output=True, text=True)

    print(result.stdout)

    if result.returncode != 0:
        print(f"Error obfuscating package: {result.stderr}")
        return False

    print("Successfully obfuscated BAID-CI package.")
    return True


def build_wheel():
    """Build a wheel from the obfuscated package"""
    print("Building wheel from obfuscated package...")

    # Copy necessary files
    shutil.copy('setup.py', 'dist/obfuscated/')
    shutil.copy('README.md', 'dist/obfuscated/')
    shutil.copy('LICENSE', 'dist/obfuscated/')

    # Build wheel
    os.chdir('dist/obfuscated')
    result = subprocess.run([
        sys.executable, '-m', 'pip', 'wheel',
        '--no-deps',
        '--wheel-dir', '..',
        '.'
    ], check=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error building wheel: {result.stderr}")
        return False

    os.chdir('../..')
    print("Successfully built wheel from obfuscated package.")
    return True


def build_executable():
    """Build a standalone executable using PyInstaller"""
    print("Building standalone executable...")

    # Use PyArmor to create a standalone executable
    result = subprocess.run([
        'pyarmor', 'pack',
        '--name', 'baid-ci',
        '--clean',
        '--output', 'dist/standalone',
        'baid_ci/cli.py'
    ], check=True, capture_output=True, text=True)

    print(result.stdout)

    if result.returncode != 0:
        print(f"Error building executable: {result.stderr}")
        return False

    print("Successfully built standalone executable.")
    return True


def main():
    """Main function"""
    if not check_pyarmor():
        return 1

    clean_dist()

    if not obfuscate_package():
        return 1

    if not build_wheel():
        return 1

    if not build_executable():
        return 1

    print("\nBuild completed successfully!")
    print("Obfuscated wheel: dist/*.whl")
    print("Standalone executable: dist/standalone/baid-ci")
    return 0


if __name__ == "__main__":
    sys.exit(main())