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
import multiprocessing

# Configuration with enhanced platform support
PLATFORMS = {
    "linux-x86_64": {
        "output": "baid-ci-linux-x86_64",
        "extra_args": ["--jobs={}".format(max(1, multiprocessing.cpu_count() - 1))]
    },
    "linux-arm64": {
        "output": "baid-ci-linux-arm64",
        "extra_args": ["--jobs={}".format(max(1, multiprocessing.cpu_count() - 1))]
    },
    "macos-x86_64": {
        "output": "baid-ci-macos-x86_64",
        "extra_args": ["--macos-create-app-bundle=no", "--jobs={}".format(max(1, multiprocessing.cpu_count() - 1))]
    },
    "macos-arm64": {
        "output": "baid-ci-macos-arm64",
        "extra_args": ["--macos-create-app-bundle=no", "--jobs={}".format(max(1, multiprocessing.cpu_count() - 1))]
    },
    "windows-x86_64": {
        "output": "baid-ci-windows-x86_64.exe",
        "extra_args": ["--windows-icon-from-ico=resources/baid-ci.ico"] if os.path.exists(
            "resources/baid-ci.ico") else []
    },
}

# Cross-platform build configurations
CROSS_COMPILE = {
    "linux-to-macos": False,  # Linux can't easily cross-compile to macOS
    "linux-to-windows": True,  # Linux can cross-compile to Windows with wine
    "macos-to-linux": False,  # macOS can't easily cross-compile to Linux
    "macos-to-windows": False,  # macOS can't easily cross-compile to Windows
}


def get_current_platform():
    """Get the current platform identifier"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        platform_id = "linux"
    elif system == "darwin":
        platform_id = "macos"
    elif system == "windows" or system.startswith("mingw") or system.startswith("msys"):
        platform_id = "windows"
    else:
        raise ValueError(f"Unsupported system: {system}")

    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64", "arm64e"):
        arch = "arm64"
    else:
        raise ValueError(f"Unsupported architecture: {machine}")

    return f"{platform_id}-{arch}"


def check_dependencies():
    """Check if all required dependencies are installed"""
    system = platform.system().lower()

    # Check for Nuitka
    ensure_nuitka_installed()

    # Check for ccache on macOS
    if system == "darwin":
        try:
            subprocess.run(["which", "ccache"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✓ ccache is installed")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("⚠️ ccache is not installed, which can speed up builds")
            print("  Install with: brew install ccache")

    # Check for patchelf on Linux
    if system == "linux":
        try:
            subprocess.run(["which", "patchelf"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✓ patchelf is installed")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("⚠️ patchelf is not installed, which may be needed for Linux builds")
            print("  Install with: sudo apt-get install patchelf (Debian/Ubuntu)")
            print("  or: sudo yum install patchelf (CentOS/RHEL/Fedora)")


def ensure_nuitka_installed():
    """Ensure Nuitka is installed"""
    try:
        subprocess.run([sys.executable, "-m", "nuitka", "--version"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✓ Nuitka is installed")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Installing Nuitka...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "nuitka>=2.7.1", "ordered-set", "pytest-runner"],
                           check=True)
            print("✓ Nuitka installed successfully")
            return True
        except subprocess.SubprocessError as e:
            print(f"✗ Failed to install Nuitka: {e}")
            return False


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

        # Make the file executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(main_file, 0o755)

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


def setup_macos_build_env():
    """Setup the macOS build environment with ccache"""
    if platform.system().lower() != "darwin":
        return {}  # Not on macOS, return empty env dict

    env = os.environ.copy()

    # Check if ccache is installed
    try:
        result = subprocess.run(["which", "ccache"], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ccache_path = result.stdout.decode('utf-8').strip()

        if ccache_path:
            # Configure ccache
            ccache_dir = os.path.expanduser("~/.ccache")
            os.makedirs(ccache_dir, exist_ok=True)

            # Configure ccache via env vars
            env["CCACHE_DIR"] = ccache_dir
            env["CCACHE_MAXSIZE"] = "5G"
            env["CCACHE_COMPRESS"] = "1"

            # Add ccache to PATH
            if platform.system().lower() == "darwin":
                # On macOS, get the libexec path
                libexec_path = subprocess.run(
                    ["brew", "--prefix", "ccache"],
                    check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                if libexec_path.returncode == 0:
                    ccache_libexec = os.path.join(
                        libexec_path.stdout.decode('utf-8').strip(),
                        "libexec"
                    )
                    env["PATH"] = f"{ccache_libexec}:{env.get('PATH', '')}"
                else:
                    # Fallback to a common location
                    env["PATH"] = f"/usr/local/opt/ccache/libexec:{env.get('PATH', '')}"

            print("✓ Configured ccache for faster builds")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("⚠️ ccache not found, proceeding with standard compilation")

    return env


def check_can_build(platform_id):
    """Check if we can build for the specified platform"""
    current = get_current_platform()
    current_os = current.split('-')[0]
    target_os = platform_id.split('-')[0]

    # Can always build for current platform
    if platform_id == current:
        return True

    # Check if cross-compilation is supported
    cross_key = f"{current_os}-to-{target_os}"
    if cross_key in CROSS_COMPILE:
        return CROSS_COMPILE[cross_key]

    # Special case: macOS can build for both arm64 and x86_64
    if current_os == "macos" and target_os == "macos":
        return True

    # Default to not supported
    return False


def build_executable(platform_id):
    """Build an executable for the specified platform"""
    if platform_id not in PLATFORMS:
        raise ValueError(f"Unknown platform: {platform_id}")

    # Check if we can build for this platform
    if not check_can_build(platform_id):
        print(f"✗ Cannot build for {platform_id} on current platform ({get_current_platform()})")
        print(f"  Cross-compilation is not supported for this combination.")
        return False

    config = PLATFORMS[platform_id]
    output_file = config["output"]
    extra_args = config["extra_args"]

    print(f"\nBuilding executable for {platform_id}...")

    # Get environment with ccache if on macOS
    env = setup_macos_build_env() if platform.system().lower() == "darwin" else os.environ.copy()

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
    ]

    # Add platform-specific options
    if platform_id.startswith("macos-"):
        # macOS specific options
        target_arch = platform_id.split('-')[1]
        current_arch = get_current_platform().split('-')[1]

        # Add target architecture if cross-compiling on macOS
        if target_arch != current_arch:
            if current_arch == "arm64" and target_arch == "x86_64":
                # Building for Intel on Apple Silicon
                cmd.append("--macos-arm64-abi=no")
            elif current_arch == "x86_64" and target_arch == "arm64":
                # Building for Apple Silicon on Intel
                print("⚠️ Cross-compiling from Intel to Apple Silicon may not produce optimal binaries")
                cmd.append("--macos-arm64-abi=yes")

    # Add platform-specific args
    cmd.extend(extra_args)

    # Add output file
    cmd.extend(["main.py", f"--output-filename={output_file}"])

    # Run the command
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, env=env)

    if result.returncode == 0:
        print(f"✓ Successfully built executable for {platform_id}")

        # Move the executable to the build directory
        output_path = Path(output_file)
        if output_path.exists():
            dest_path = Path("build") / output_file
            shutil.move(output_path, dest_path)
            print(f"✓ Moved executable to {dest_path}")

            # Make the file executable on Unix-like systems
            if not platform_id.startswith("windows"):
                os.chmod(dest_path, 0o755)
                print(f"✓ Set executable permissions")
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

    # Display current platform
    current_platform = get_current_platform()
    print(f"Current platform: {current_platform}")

    # Check dependencies
    check_dependencies()

    # Determine which platform to build for
    if len(sys.argv) > 1:
        requested_platforms = sys.argv[1:]

        # Handle "all" option
        if "all" in requested_platforms:
            print("Building for all supported platforms")
            platforms_to_build = []
            for platform_id in PLATFORMS.keys():
                if check_can_build(platform_id):
                    platforms_to_build.append(platform_id)
                else:
                    print(f"⚠️ Skipping {platform_id} - cross-compilation not supported")
        else:
            # Filter only valid platforms
            platforms_to_build = [p for p in requested_platforms if p in PLATFORMS]
            if not platforms_to_build:
                print(f"Error: No valid platforms specified. Available platforms: {', '.join(PLATFORMS.keys())}")
                return 1
    else:
        # If no platform specified, build for current platform
        if current_platform in PLATFORMS:
            platforms_to_build = [current_platform]
            print(f"No platform specified, building for current platform: {current_platform}")
        else:
            print(f"Error: Current platform {current_platform} is not supported for building")
            return 1

    create_main_entry_point()
    clean_build_directory()

    # Build executables for each platform
    success = True
    built_platforms = []
    failed_platforms = []

    for platform_id in platforms_to_build:
        if build_executable(platform_id):
            built_platforms.append(platform_id)
        else:
            failed_platforms.append(platform_id)
            success = False

    # Print summary
    print("\n=========================")
    print("Build Summary")
    print("=========================")

    if built_platforms:
        print(f"✅ Successfully built executables for: {', '.join(built_platforms)}")
        print(f"   Executables can be found in the 'build/' directory")

    if failed_platforms:
        print(f"❌ Failed to build executables for: {', '.join(failed_platforms)}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())