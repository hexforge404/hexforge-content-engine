install_a1111() {
  echo -e "\n🚀 Installing AUTOMATIC1111 Stable Diffusion (as devuser)..."

  sudo -u devuser bash -c '
    set -e
    cd ~
    mkdir -p ~/ai-tools
    cd ~/ai-tools

    if [ -d "stable-diffusion-webui" ]; then
      echo "ℹ️  [A1111] Directory already exists. Skipping clone."
      exit 0
    fi

    git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
    cd stable-diffusion-webui
    echo "📂 [A1111] Repository cloned."

    # Initial run to trigger dependency install
    echo "📦 [A1111] Running preload (webui.sh --exit)..."
    bash webui.sh --exit
  '

  log_success "AUTOMATIC1111"
}
