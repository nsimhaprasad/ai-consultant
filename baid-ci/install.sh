#!/bin/bash
# BAID-CI Installation Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="/usr/local/bin"
DEFAULT_VERSION="latest"
VERSION="$DEFAULT_VERSION"

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}         BAID-CI Installation Tool         ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
}

print_usage() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Options:"
    echo -e "  -v, --version VERSION    Specify version to install (default: latest)"
    echo -e "  -d, --dir DIRECTORY      Specify installation directory (default: /usr/local/bin)"
    echo -e "  -h, --help               Display this help message"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -d|--dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -h|--help)
            print_header
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

print_header

# Determine OS and architecture
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
    linux)
        PLATFORM="linux"
        ;;
    darwin)
        PLATFORM="macos"
        ;;
    msys*|mingw*|cygwin*)
        PLATFORM="windows"
        ;;
    *)
        echo -e "${RED}Error: Unsupported operating system: $OS${NC}"
        exit 1
        ;;
esac

case "$ARCH" in
    x86_64|amd64)
        ARCHITECTURE="x86_64"
        ;;
    arm64|aarch64)
        ARCHITECTURE="arm64"
        ;;
    *)
        echo -e "${RED}Error: Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

# Determine file extension
if [ "$PLATFORM" = "windows" ]; then
    EXT=".exe"
else
    EXT=""
fi

echo -e "${BLUE}Detected platform:${NC} $PLATFORM-$ARCHITECTURE"

# Determine the download URL
if [ "$VERSION" = "latest" ]; then
    echo -e "${BLUE}Fetching latest release information...${NC}"
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Error: curl is required for installation${NC}"
        exit 1
    fi

    # Get the latest release tag from GitHub API
    LATEST_RELEASE=$(curl -s https://api.github.com/repos/beskar-ai/baid-ci/releases/latest)
    if [ -z "$LATEST_RELEASE" ]; then
        echo -e "${RED}Error: Failed to fetch latest release information${NC}"
        exit 1
    fi

    VERSION=$(echo "$LATEST_RELEASE" | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4)
    if [ -z "$VERSION" ]; then
        echo -e "${RED}Error: Failed to determine latest version${NC}"
        exit 1
    fi
    echo -e "${GREEN}Latest version: $VERSION${NC}"
fi

# Construct the download URL (adjust according to your GitHub release structure)
FILENAME="baid-ci-$PLATFORM-$ARCHITECTURE$EXT"
DOWNLOAD_URL="https://github.com/nsimhaprasad/ai-consultant/releases/download/$VERSION/$FILENAME"

echo -e "${BLUE}Downloading BAID-CI $VERSION for $PLATFORM-$ARCHITECTURE...${NC}"
echo -e "${BLUE}Download URL: $DOWNLOAD_URL${NC}"

# Create a temporary directory
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Download the binary
if ! curl -L -o "$TMP_DIR/$FILENAME" "$DOWNLOAD_URL"; then
    echo -e "${RED}Error: Failed to download BAID-CI${NC}"
    exit 1
fi

# Make the binary executable (not needed for Windows)
if [ "$PLATFORM" != "windows" ]; then
    chmod +x "$TMP_DIR/$FILENAME"
fi

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Creating installation directory: $INSTALL_DIR${NC}"
    if ! mkdir -p "$INSTALL_DIR"; then
        echo -e "${RED}Error: Failed to create installation directory${NC}"
        echo -e "${YELLOW}Try running with sudo:${NC} sudo $0 $*"
        exit 1
    fi
fi

# Install the binary
echo -e "${BLUE}Installing to $INSTALL_DIR/baid-ci$EXT...${NC}"
if ! mv "$TMP_DIR/$FILENAME" "$INSTALL_DIR/baid-ci$EXT"; then
    echo -e "${RED}Error: Failed to install BAID-CI${NC}"
    echo -e "${YELLOW}Try running with sudo:${NC} sudo $0 $*"
    exit 1
fi

echo -e "${GREEN}BAID-CI $VERSION has been successfully installed!${NC}"
echo -e "${GREEN}You can now run it with:${NC} baid-ci"

# Check if the installation directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}Warning: $INSTALL_DIR is not in your PATH${NC}"
    echo -e "You may need to add it to your PATH or use the full path to run BAID-CI."
fi

echo
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${BLUE}============================================${NC}"