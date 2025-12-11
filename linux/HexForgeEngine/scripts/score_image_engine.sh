#!/bin/bash
set -euo pipefail

# Base paths
BASE="/mnt/hdd-storage/hexforge-content-engine"
VENV="${BASE}/venv/bin/activate"

# Directory of this script (…/linux/HexForgeEngine/scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCORE_PY="${SCRIPT_DIR}/score_image.py"

# Log file for stderr from the scoring engine
LOG_DIR="${BASE}/logs/score-engine"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/score_image_engine.log"

# Debug info (sent to stderr so it doesn't pollute JSON stdout)
echo "[score] Using SCORE_PY=${SCORE_PY}" >&2
echo "[score] Logging stderr to ${LOG_FILE}" >&2

if [ ! -f "$SCORE_PY" ]; then
  echo "[score] ERROR: score_image.py not found at ${SCORE_PY}" >&2
  exit 1
fi

# Activate venv
# shellcheck source=/dev/null
source "$VENV"

# IMPORTANT:
#   - Stdout MUST be *pure JSON* from score_image.py
#   - Stderr is appended to the log file
python "$SCORE_PY" "$@" 2>>"$LOG_FILE"
