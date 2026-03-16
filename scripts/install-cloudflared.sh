#!/usr/bin/env bash
# Install cloudflared for Quick Tunnels (public share link). Run on the device.
set -e

ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  armv7l)  ARCH="arm" ;;
  *) echo "Unsupported arch: $ARCH"; exit 1 ;;
esac

VERSION="2024.2.0"
URL="https://github.com/cloudflare/cloudflared/releases/download/${VERSION}/cloudflared-linux-${ARCH}"
DEST="${1:-/usr/local/bin/cloudflared}"

echo "Downloading cloudflared ${VERSION} for ${ARCH}..."
sudo curl -L -o "$DEST" "$URL"
sudo chmod +x "$DEST"
echo "Installed to $DEST"
"$DEST" --version
