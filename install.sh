#!/usr/bin/env bash
set -e

echo "🐸 Installing CronFrog..."

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

if [ "$ARCH" = "x86_64" ]; then
    ARCH="amd64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    ARCH="arm64"
fi

if [ "$OS" = "linux" ]; then
    BINARY_NAME="cronfrog-linux"
elif [ "$OS" = "darwin" ]; then
    BINARY_NAME="cronfrog-macos"
else
    echo "Unsupported OS: $OS"
    exit 1
fi

INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# Download the latest binary from GitHub Releases
REPO="shayansaha85/cronfrog"
LATEST_URL=$(curl -s https://api.github.com/repos/$REPO/releases/latest | grep "browser_download_url.*$BINARY_NAME" | cut -d : -f 2,3 | tr -d \")

# Clean up leading/trailing spaces in URL
LATEST_URL=$(echo "$LATEST_URL" | xargs)

if [ -z "$LATEST_URL" ]; then
    echo "Could not find a release for your platform ($BINARY_NAME)."
    echo "Make sure you have created a GitHub Release with the correct binaries."
    exit 1
fi

echo "Downloading from $LATEST_URL..."
curl -sSL "$LATEST_URL" -o "$INSTALL_DIR/cronfrog"
chmod +x "$INSTALL_DIR/cronfrog"

echo "✅ CronFrog installed to $INSTALL_DIR/cronfrog"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "Adding $INSTALL_DIR to PATH in ~/.bashrc and ~/.zshrc..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    if [ -f "$HOME/.zshrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
    echo "Please run 'source ~/.bashrc' or restart your terminal to use the 'cronfrog' command."
else
    echo "You can now run 'cronfrog' from your terminal."
fi