#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'USAGE'
Install Somnia Auditor binary on Linux or macOS.

Usage:
  ./scripts/install_binary.sh [path-to-binary]

Examples:
  # Install from local build output
  ./scripts/install_binary.sh dist/somnia-auditor

  # Auto-detect from ./dist (default)
  ./scripts/install_binary.sh

Notes:
  - Installs to /usr/local/bin if writable; otherwise falls back to ~/.local/bin.
  - Requires an already-built binary (see: python build_binary.py).
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$OS" in
  linux*|darwin*) ;;
  *) echo "Unsupported OS: $OS" >&2; exit 1;;
esac

BIN_NAME="somnia-auditor"

# Resolve source binary
SRC_BIN="${1:-}"
if [[ -z "$SRC_BIN" ]]; then
  if [[ -x "dist/$BIN_NAME" ]]; then
    SRC_BIN="dist/$BIN_NAME"
  else
    echo "Binary not found. Build it first: python build_binary.py" >&2
    echo "Or provide a path to the binary: ./scripts/install_binary.sh /path/to/$BIN_NAME" >&2
    exit 1
  fi
fi

if [[ ! -f "$SRC_BIN" ]]; then
  echo "Source binary does not exist: $SRC_BIN" >&2
  exit 1
fi

chmod +x "$SRC_BIN" || true

# Choose install directory
INSTALL_DIR="/usr/local/bin"
if [[ ! -w "$INSTALL_DIR" ]]; then
  # Fallback to user bin
  INSTALL_DIR="$HOME/.local/bin"
  mkdir -p "$INSTALL_DIR"
  echo "Using user install directory: $INSTALL_DIR"
fi

TARGET="$INSTALL_DIR/$BIN_NAME"

echo "Installing $BIN_NAME to $TARGET"
if command -v install >/dev/null 2>&1; then
  install -m 0755 "$SRC_BIN" "$TARGET"
else
  cp "$SRC_BIN" "$TARGET"
  chmod 0755 "$TARGET"
fi

# On macOS, remove quarantine attribute if present
if [[ "$OS" == "darwin" ]] && command -v xattr >/dev/null 2>&1; then
  xattr -d com.apple.quarantine "$TARGET" 2>/dev/null || true
fi

# Ensure install dir is on PATH for this session
if ! command -v "$BIN_NAME" >/dev/null 2>&1; then
  case ":$PATH:" in
    *:"$INSTALL_DIR":*) ;;
    *) echo "Note: $INSTALL_DIR is not on PATH. Add this to your shell profile:";
       echo "  export PATH=\"$INSTALL_DIR:\$PATH\"";
       ;;
  esac
fi

echo "Verifying installation..."
if "$TARGET" --version >/dev/null 2>&1; then
  echo "✓ Installed: $TARGET"
  echo -n "Version: "; "$TARGET" --version
else
  echo "Installed, but could not run '$BIN_NAME --version'." >&2
  echo "Check dependencies or run the binary directly: $TARGET" >&2
fi

exit 0


