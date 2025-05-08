#!/usr/bin/env python3
"""
Build script for creating Nuitka-compiled executables for BAID-CI
Generates platform-specific binaries for distribution
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# Configuration
PLATFORMS = {
    "linux-x86_64": {
        "output": "baid-ci-linux-x86_64",
        "extra_args": []
    },
    "linux-arm64": {
        "output": "baid-ci-linux-arm64",
        "extra_args": []
    },
    "macos-x86_64": {
        "output": "baid-ci-macos-x86_64",
        "extra_args": []
    },
    "macos-arm64": {
        "output": "baid-ci-macos-arm64",
        "extra_args": []
    },
    "windows-x86_64": {
        "output": "baid-ci-windows-x86_64.exe",
        "extra_args": []
    },
}


def get_current_platform():
    """Get the current platform identifier"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        platform_id = "linux"
    elif system == "darwin":
        platform_id = "macos"
    elif system == "windows":
        platform_id = "windows"
    else:
        raise ValueError(f"Unsupported system: {system}")

    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise ValueError(f"Unsupported architecture: {machine}")

    return f"{platform_id}-{arch}"


def ensure_nuitka_installed():
    """Ensure Nuitka is installed"""
    try:
        subprocess.run([sys.executable, "-m", "nuitka", "--version"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✓ Nuitka is installed")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Installing Nuitka...")
        subprocess.run([sys.executable, "-m", "pip", "install", "nuitka", "ordered-set", "pytest-runner"],
                       check=True)
        print("✓ Nuitka installed successfully")


def create_main_entry_point():
    """Create a main.py entry point if it doesn't exist"""
    main_file = Path("main.py")

    if not main_file.exists():
        print("Creating main.py entry point...")

        with open(main_file, "w") as f:
            f.write("""#!/usr/bin/env python3
# Entry point for BAID-CI
import sys
from baid_ci.cli import main

if __name__ == "__main__":
    sys.exit(main())
""")

        print("✓ Created main.py entry point")
    else:
        print("✓ main.py entry point already exists")


def clean_build_directory():
    """Clean the build directory"""
    build_dir = Path("build")
    if build_dir.exists():
        print(f"Cleaning build directory...")
        shutil.rmtree(build_dir)

    build_dir.mkdir(exist_ok=True)
    print("✓ Build directory cleaned")


def build_executable(platform_id):
    """Build an executable for the specified platform"""
    if platform_id not in PLATFORMS:
        raise ValueError(f"Unknown platform: {platform_id}")

    config = PLATFORMS[platform_id]
    output_file = config["output"]
    extra_args = config["extra_args"]

    print(f"\nBuilding executable for {platform_id}...")

    # Base command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--follow-imports",
        "--include-package=baid_ci",
        "--remove-output",
        "--lto=yes",
        "--plugin-enable=anti-bloat",
        "--prefer-source-code",
        "--no-pyi-file",
        *extra_args,
        "main.py",
        f"--output-filename={output_file}"
    ]

    # Run the command
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print(f"✓ Successfully built executable for {platform_id}")

        # Move the executable to the build directory
        output_path = Path(output_file)
        if output_path.exists():
            dest_path = Path("build") / output_file
            shutil.move(output_path, dest_path)
            print(f"✓ Moved executable to {dest_path}")
        else:
            print(f"Warning: Expected output file {output_file} not found")
            return False

        return True
    else:
        print(f"✗ Failed to build executable for {platform_id}")
        return False


def main():
    """Main function"""
    print("BAID-CI Executable Builder")
    print("=========================")

    # Determine which platform to build for
    if len(sys.argv) > 1:
        platforms_to_build = [p for p in sys.argv[1:] if p in PLATFORMS]
        if not platforms_to_build:
            print(f"Error: No valid platforms specified. Available platforms: {', '.join(PLATFORMS.keys())}")
            return 1
    else:
        # If no platform specified, build for current platform
        current_platform = get_current_platform()
        if current_platform in PLATFORMS:
            platforms_to_build = [current_platform]
            print(f"No platform specified, building for current platform: {current_platform}")
        else:
            print(f"Error: Current platform {current_platform} is not supported for building")
            return 1

    ensure_nuitka_installed()
    create_main_entry_point()
    clean_build_directory()

    # Build executables for each platform
    success = True
    for platform_id in platforms_to_build:
        if not build_executable(platform_id):
            success = False

    if success:
        print("\n✓ All executables built successfully!")
        print(f"Executables can be found in the 'build/' directory")
    else:
        print("\n✗ Some executables failed to build")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())