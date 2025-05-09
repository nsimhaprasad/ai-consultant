#!/bin/bash
# BAID-CI Installation Script - Simplified Version
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="/usr/local/bin"
DEFAULT_VERSION="baid-ci-v0.1.2"
VERSION="$DEFAULT_VERSION"
REPO_URL="https://github.com/nsimhaprasad/ai-consultant"

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}         BAID-CI Installation Tool         ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
}

print_usage() {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Options:"
    echo -e "  -v, --version VERSION    Specify version to install (default: $DEFAULT_VERSION)"
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

# For macOS, use x86_64 on both Intel and Apple Silicon
if [ "$PLATFORM" = "macos" ]; then
    ARCHITECTURE="x86_64"
    if [ "$ARCH" = "arm64" ]; then
        echo -e "${YELLOW}Detected Apple Silicon (arm64).${NC}"
        echo -e "${YELLOW}Using x86_64 binary with Rosetta 2 translation.${NC}"
    fi
else
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
fi

# Determine file extension
if [ "$PLATFORM" = "windows" ]; then
    EXT=".exe"
else
    EXT=""
fi

echo -e "${BLUE}Detected platform:${NC} $PLATFORM-$ARCHITECTURE"

# Construct the download URL - now using simplified tag format
FILENAME="baid-ci-$PLATFORM-$ARCHITECTURE$EXT"
DOWNLOAD_URL="$REPO_URL/releases/download/$VERSION/$FILENAME"

echo -e "${BLUE}Downloading BAID-CI ($VERSION) for $PLATFORM-$ARCHITECTURE...${NC}"
echo -e "${BLUE}Download URL: $DOWNLOAD_URL${NC}"

# Create a temporary directory
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Download the binary with proper error handling
HTTP_STATUS=$(curl -s -L -w "%{http_code}" -o "$TMP_DIR/$FILENAME" "$DOWNLOAD_URL")

if [ "$HTTP_STATUS" != "200" ]; then
    echo -e "${RED}Error: Failed to download binary (HTTP status: $HTTP_STATUS)${NC}"
    echo -e "${RED}The URL may be incorrect or inaccessible.${NC}"
    exit 1
fi

# Check if the file is very small (likely an error message)
FILE_SIZE=$(stat -f%z "$TMP_DIR/$FILENAME" 2>/dev/null || stat -c%s "$TMP_DIR/$FILENAME")
if [ "$FILE_SIZE" -lt 1000 ]; then  # Less than 1KB is suspicious
    echo -e "${RED}Warning: Downloaded file is very small ($FILE_SIZE bytes)${NC}"
    echo -e "${RED}Content of the downloaded file:${NC}"
    cat "$TMP_DIR/$FILENAME"
    echo
    echo -e "${RED}This doesn't look like a valid binary. Aborting installation.${NC}"
    exit 1
fi

# Check file type
FILE_TYPE=$(file "$TMP_DIR/$FILENAME")
echo -e "${BLUE}File type:${NC} $FILE_TYPE"

# Make the binary executable
chmod +x "$TMP_DIR/$FILENAME"

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Creating installation directory: $INSTALL_DIR${NC}"
    if ! mkdir -p "$INSTALL_DIR"; then
        echo -e "${RED}Error: Failed to create installation directory${NC}"
        echo -e "${YELLOW}Try running with sudo:${NC} sudo bash -c \"$(curl -fsSL https://gist.githubusercontent.com/nsimhaprasad/5a2aa9f91b855c6792a96132887769df/raw/install.sh)\""
        exit 1
    fi
fi

# Install the binary
echo -e "${BLUE}Installing to $INSTALL_DIR/baid-ci$EXT...${NC}"
if ! mv "$TMP_DIR/$FILENAME" "$INSTALL_DIR/baid-ci$EXT"; then
    echo -e "${RED}Error: Failed to install BAID-CI${NC}"
    echo -e "${YELLOW}Try running with sudo:${NC} sudo bash -c \"$(curl -fsSL https://gist.githubusercontent.com/nsimhaprasad/5a2aa9f91b855c6792a96132887769df/raw/install.sh)\""
    exit 1
fi

echo -e "${GREEN}BAID-CI $VERSION has been successfully installed!${NC}"
echo -e "${GREEN}You can now run it with:${NC} baid-ci"

# Check if the installation directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}Warning: $INSTALL_DIR is not in your PATH${NC}"

    # Suggest appropriate command to add to PATH based on shell
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
        bash)
            echo -e "Run this command to add it to your PATH:${NC}"
            echo -e "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
            ;;
        zsh)
            echo -e "Run this command to add it to your PATH:${NC}"
            echo -e "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
            ;;
        *)
            echo -e "Add $INSTALL_DIR to your PATH to run baid-ci without specifying the full path."
            ;;
    esac
fi

echo
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${BLUE}============================================${NC}"