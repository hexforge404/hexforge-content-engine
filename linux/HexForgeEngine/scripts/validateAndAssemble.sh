#!/bin/bash

# 🧪 Validate if required session assets exist before launching screen reader step

PROJECT="$1"
PART="$2"

# Check if both project and part are passed in
if [[ -z "$PROJECT" || -z "$PART" ]]; then
  echo "❌ Usage: $0 <project> <part>"
  exit 1
fi

# Define base and asset directories
BASE_DIR="/mnt/hdd-storage/hexforge-content-engine"
ASSET_DIR="$BASE_DIR/Assets/$PROJECT/$PART"

# Look for expected asset files
WINDOWS_LOG="$(find "$ASSET_DIR" -iname '*windows*.log' | head -n1)"
LINUX_LOG="$(find "$BASE_DIR/logs/HexForge_Content_Engine" -iname "*session*.log" -newermt "1 hour ago" | tail -n1)"
VIDEO_FILE="$(find "$ASSET_DIR" -iname '*.mkv' | head -n1)"
SCREENSHOTS=("$ASSET_DIR"/*.png)

VALID=true

# Check for Windows log
if [[ -z "$WINDOWS_LOG" ]]; then
  echo "❌ Missing Windows log file."
  VALID=false
else
  echo "✅ Found Windows log: $WINDOWS_LOG"
fi

# Check for recent Linux log
if [[ -z "$LINUX_LOG" ]]; then
  echo "❌ Missing recent Linux log file."
  VALID=false
else
  echo "✅ Found Linux log: $LINUX_LOG"
fi

# Check for screen recording video
if [[ -z "$VIDEO_FILE" ]]; then
  echo "❌ Missing video file (.mkv)."
  VALID=false
else
  echo "✅ Found video: $VIDEO_FILE"
fi

# Check for any screenshots
if [[ ! -e "${SCREENSHOTS[0]}" ]]; then
  echo "❌ No screenshots (.png) found."
  VALID=false
else
  echo "✅ Screenshots detected: ${#SCREENSHOTS[@]}"
fi

# If any required asset is missing, abort
if [ "$VALID" = false ]; then
  echo "⚠️ Validation failed. Aborting assembly."
  exit 1
fi

# Define target directory for combined inputs
FINAL_ASSEMBLY="$BASE_DIR/input"

# Copy validated files to central input directory
cp "$WINDOWS_LOG" "$FINAL_ASSEMBLY/session_windows.log"
echo "📁 Copied Windows log to input directory."

cp "$LINUX_LOG" "$FINAL_ASSEMBLY/session_linux.log"
echo "📁 Copied Linux log to input directory."

cp "$VIDEO_FILE" "$FINAL_ASSEMBLY/session_video.mkv"
echo "📁 Copied video file to input directory."

cp "$ASSET_DIR"/*.png "$FINAL_ASSEMBLY/" 2>/dev/null && echo "📸 Screenshots copied to input directory."
cp "$ASSET_DIR"/*.txt "$FINAL_ASSEMBLY/" 2>/dev/null && echo "📝 Text notes copied to input directory."

# ✅ Trigger screen text extraction step (runs OCR + timestamp matching)
echo "📦 All required assets copied to input/ directory. Proceeding to screen reader..."
echo "🚀 Launching screen text extraction..."
node "$BASE_DIR/scripts/extractScreenTextFromVideo.js"

exit 0
