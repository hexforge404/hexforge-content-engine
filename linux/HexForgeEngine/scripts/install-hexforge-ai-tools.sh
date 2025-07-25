#!/bin/bash

# install-hexforge-ai-tools.sh
# Full install script for HexForge AI tools
# Includes: ComfyUI, SadTalker, Wav2Lip, AUTOMATIC1111
# Ensures correct ownership and paths for both root and devuser

set -e  # Exit immediately if a command exits with a non-zero status

TOOLS_DIR="$HOME/ai-tools"  # Directory where all tools will be installed
INSTALL_AS_USER="devuser"    # Non-root user to install AUTOMATIC1111 under

# Logging functions for consistent output formatting
log() {
    echo -e "\033[1;32m[+] $1\033[0m"
}

warn() {
    echo -e "\033[1;33m[!] $1\033[0m"
}

error() {
    echo -e "\033[1;31m[-] $1\033[0m" >&2
}

# Create the tools directory if it doesn't exist
log "Creating tools directory at $TOOLS_DIR..."
mkdir -p "$TOOLS_DIR"

# === 1. SYSTEM DEPENDENCIES ===
log "Installing core system dependencies..."
apt-get update
apt-get install -y git python3 python3-venv ffmpeg wget unzip
log "System dependencies installed."

# === 2. TEST PYTHON ENVIRONMENT ===
log "Creating test virtualenv to check pip and Python..."
python3 -m venv "$TOOLS_DIR/_venv-check"  # Used to confirm pip setup
source "$TOOLS_DIR/_venv-check/bin/activate"
log "Upgrading pip in test venv..."
pip install --upgrade pip > /dev/null  # Quietly upgrade pip inside venv
log "✅ pip upgraded inside venv"
deactivate

# === 3. INSTALL AUTOMATIC1111 under devuser ===
log "Installing AUTOMATIC1111 as $INSTALL_AS_USER..."
sudo -u $INSTALL_AS_USER bash <<EOF
mkdir -p /home/$INSTALL_AS_USER/ai-tools && cd /home/$INSTALL_AS_USER/ai-tools
if [ ! -d stable-diffusion-webui ]; then
    echo "Cloning AUTOMATIC1111 repo..."
    git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
else
    echo "AUTOMATIC1111 already exists, skipping clone."
fi
EOF
log "✅ [AUTOMATIC1111] installed or already present."

# === 4. COMFYUI INSTALL ===
log "Installing ComfyUI..."
cd "$TOOLS_DIR"
if [ ! -d ComfyUI ]; then
    echo "Cloning ComfyUI repository..."
    git clone https://github.com/comfyanonymous/ComfyUI.git  # Clone repo
    echo "Creating ComfyUI virtual environment..."
    python3 -m venv ComfyUI/venv                            # Create virtualenv
    source ComfyUI/venv/bin/activate
    echo "Installing ComfyUI dependencies..."
    pip install -r ComfyUI/requirements.txt                # Install dependencies
    deactivate
    log "✅ ComfyUI installed."
else
    warn "ComfyUI already exists, skipping."
fi

# === 5. SADTALKER INSTALL ===
log "Installing SadTalker..."
cd "$TOOLS_DIR"
if [ ! -d SadTalker ]; then
    echo "Cloning SadTalker repository..."
    git clone https://github.com/OpenTalker/SadTalker.git   # Clone repo
    echo "Creating SadTalker virtual environment..."
    python3 -m venv SadTalker/venv                          # Create virtualenv
    source SadTalker/venv/bin/activate
    echo "Upgrading pip for SadTalker..."
    pip install --upgrade pip
    echo "Installing SadTalker dependencies (with fallback for OpenCV)..."
    pip install -r SadTalker/requirements.txt || pip install opencv-python==4.5.5.64
    deactivate
    log "✅ SadTalker installed."
else
    warn "SadTalker already exists, skipping."
fi

# === 6. WAV2LIP INSTALL ===
log "Installing Wav2Lip..."
cd "$TOOLS_DIR"
if [ ! -d Wav2Lip ]; then
    echo "Cloning Wav2Lip repository..."
    git clone https://github.com/Rudrabha/Wav2Lip.git       # Clone repo
    echo "Creating Wav2Lip virtual environment..."
    python3 -m venv Wav2Lip/venv                            # Create virtualenv
    source Wav2Lip/venv/bin/activate
    echo "Installing Wav2Lip dependencies..."
    pip install -r Wav2Lip/requirements.txt                # Install dependencies
    deactivate
    log "✅ Wav2Lip installed."
else
    warn "Wav2Lip already exists, skipping."
fi

log "✅ All HexForge AI tools installed."
echo "Run them individually using their respective launch scripts or interfaces."
