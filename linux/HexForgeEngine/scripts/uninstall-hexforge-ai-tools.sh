#!/bin/bash

# uninstall-hexforge-ai-tools.sh
# Removes all installed HexForge AI tools
# Cleans up both root and devuser installations

TOOLS_DIR="$HOME/ai-tools"
DEVUSER="devuser"
DEV_TOOLS_DIR="/home/$DEVUSER/ai-tools"

log() {
    echo -e "\033[1;31m[-] $1\033[0m"
}

confirm() {
    read -p "Are you sure you want to remove ALL installed AI tools? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborting."
        exit 1
    fi
}

confirm

log "Removing ComfyUI..."
rm -rf "$TOOLS_DIR/ComfyUI"

log "Removing SadTalker..."
rm -rf "$TOOLS_DIR/SadTalker"

log "Removing Wav2Lip..."
rm -rf "$TOOLS_DIR/Wav2Lip"

log "Removing system test virtualenv..."
rm -rf "$TOOLS_DIR/_venv-check"

if id "$DEVUSER" &>/dev/null; then
    log "Removing AUTOMATIC1111 from $DEVUSER..."
    sudo rm -rf "$DEV_TOOLS_DIR/stable-diffusion-webui"
else
    log "User $DEVUSER not found. Skipping AUTOMATIC1111 uninstall."
fi

log "✅ All HexForge AI tools removed."
