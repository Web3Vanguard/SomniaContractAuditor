#!/usr/bin/env bash

set -euo pipefail

# Remote-friendly installer for Somnia Auditor.
# Intended usage:
#   curl -fsSL https://raw.githubusercontent.com/Web3Vanguard/SomniaContractAuditor/refs/heads/main/scripts/install.sh | bash
# or
#   curl -fsSL https://raw.githubusercontent.com/Web3Vanguard/SomniaContractAuditor/refs/heads/main/scripts/install.sh | sudo bash

BIN_NAME="somnia-auditor"
DEFAULT_INSTALL_DIR="/usr/local/bin"
FALLBACK_INSTALL_DIR="$HOME/.local/bin"

progress_bar() {
  local progress=$1
  local total=100
  local width=40
  local filled=$(( progress * width / total ))
  local empty=$(( width - filled ))
  printf "\r["
  printf "%0.s#" $(seq 1 $filled)
  printf "%0.s-" $(seq 1 $empty)
  printf "] %d%%" "$progress"
}

run_with_progress() {
  local duration=$1
  local message=$2
  echo -ne "\n$message"
  for i in $(seq 1 100); do
    progress_bar "$i"
    sleep "$(bc <<< "$duration/100")"
  done
  echo ""
}

# Compute OS and ARCH
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64|amd64) ARCH="x86_64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  armv7l) ARCH="armv7" ;;
  *) ARCH="$ARCH_RAW" ;;
esac

case "$OS" in
  linux)   ASSET_OS="linux" ;;
  darwin)  ASSET_OS="macos" ;;
  *) echo "Unsupported OS: $OS" >&2; exit 1 ;;
esac

# Where to download from. You can bake this env at deploy time.
# If you publish GitHub releases named like: somnia-auditor-<os>-<arch>
# this default will work out of the box.
BASE_URL="${SOMNIA_BASE_URL:-https://github.com/Web3Vanguard/SomniaContractAuditor/releases/latest/download}"
ASSET_NAME="${BIN_NAME}-${ASSET_OS}-${ARCH}"
DOWNLOAD_URL="${BASE_URL}/${ASSET_NAME}"

echo "🔍 Installing ${BIN_NAME} for ${ASSET_OS}/${ARCH}"
echo "📦 Source: ${DOWNLOAD_URL}"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

TARGET_TMP="$TMP_DIR/$BIN_NAME"

echo "⬇️  Downloading binary..."
if ! curl -fsSL "$DOWNLOAD_URL" -o "$TARGET_TMP"; then
  echo "Download failed from: $DOWNLOAD_URL" >&2
  echo "Tip: ensure the release asset exists with this name or set SOMNIA_BASE_URL to your hosting path." >&2
  exit 1
fi

chmod +x "$TARGET_TMP"

# Decide install dir: prefer /usr/local/bin; if not writable, try sudo; else fallback to ~/.local/bin
INSTALL_DIR="$DEFAULT_INSTALL_DIR"

install_with() {
  local dest="$1"
  echo "📂 Installing to $dest..."
  if command -v install >/dev/null 2>&1; then
    install -m 0755 "$TARGET_TMP" "$dest/$BIN_NAME"
  else
    cp "$TARGET_TMP" "$dest/$BIN_NAME"
    chmod 0755 "$dest/$BIN_NAME"
  fi
}

echo "⚙️  Setting up binary..."
run_with_progress 1.5 "Installing..."

if [[ -w "$INSTALL_DIR" ]]; then
  install_with "$INSTALL_DIR"
else
  if command -v sudo >/dev/null 2>&1; then
    echo "🔐 Using sudo for install..."
    run_with_progress 1 "Authorizing..."
    
    if command -v install >/dev/null 2>&1; then
      sudo install -m 0755 "$TARGET_TMP" "$INSTALL_DIR/$BIN_NAME"
    else
      sudo cp "$TARGET_TMP" "$INSTALL_DIR/$BIN_NAME"
      sudo chmod 0755 "$INSTALL_DIR/$BIN_NAME"
    fi
  else
    echo "⚠️  No write access to $INSTALL_DIR; falling back to user dir: $FALLBACK_INSTALL_DIR"

    mkdir -p "$FALLBACK_INSTALL_DIR"
    install_with "$FALLBACK_INSTALL_DIR"
    case ":$PATH:" in
      *:"$FALLBACK_INSTALL_DIR":*) ;;
      *) echo "💡 Add to PATH: export PATH=\"$FALLBACK_INSTALL_DIR:\$PATH\"";;
    esac
  fi
fi

INSTALLED_PATH="$DEFAULT_INSTALL_DIR/$BIN_NAME"
if [[ ! -x "$INSTALLED_PATH" ]]; then
  INSTALLED_PATH="$FALLBACK_INSTALL_DIR/$BIN_NAME"
fi

# macOS quarantine fix (best-effort)
if [[ "$OS" == "darwin" ]] && command -v xattr >/dev/null 2>&1; then
  xattr -d com.apple.quarantine "$INSTALLED_PATH" 2>/dev/null || true
fi

echo "🔍 Verifying installation..."
run_with_progress 1 "Checking binary..."
if "$INSTALLED_PATH" --version >/dev/null 2>&1; then
  echo -e "\n✅ Installed successfully!"
  echo "📍 Location: $INSTALLED_PATH"
  echo -n "🧩 Version: "; "$INSTALLED_PATH" --version
else
  echo "⚠️  Installed, but could not run '$BIN_NAME --version'." >&2
  echo "Try running directly: $INSTALLED_PATH" >&2
fi

echo "🎉 Done!"
exit 0


