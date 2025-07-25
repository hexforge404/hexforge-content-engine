#!/bin/bash

# 🌐 Entry point for the Linux-side HexForge Content Pipeline
echo "🌐 Starting HexForge Linux Content Pipeline"

# Step 1: Start CLI session logger (records terminal output into timestamped log)
echo "🧠 Launching shell logger..."
/usr/local/bin/hexforge-shell.sh
if [ $? -ne 0 ]; then
  echo "❌ Failed to launch shell logger. Exiting."
  exit 1
fi

# Step 2: Extract visible text from the latest screen recording using OCR
echo "🔍 Extracting screen text from video..."
node /mnt/hdd-storage/hexforge-content-engine/scripts/extractScreenTextFromVideo.js
if [ $? -ne 0 ]; then
  echo "❌ Failed to extract screen text. Exiting."
  exit 1
fi

# Step 3: Build a JSON object combining log, chat, screen text into blog metadata
echo "🗞️ Building blog JSON from session..."
node /mnt/hdd-storage/hexforge-content-engine/scripts/buildBlogJsonFromSession.js
if [ $? -ne 0 ]; then
  echo "❌ Failed to build blog JSON. Exiting."
  exit 1
fi

# Step 4: Use the blog.json input to generate a markdown draft via local AI model
echo "✍️ Generating blog draft..."
node /mnt/hdd-storage/hexforge-content-engine/scripts/generateBlogFromJSON.js
if [ $? -ne 0 ]; then
  echo "❌ Blog generation failed. Exiting."
  exit 1
fi

# Step 5: Copy blog.md to central output directory
echo "🗃️ Copying blog.md to output directory..."

# Extract project and part names from latest session folder
SESSION_DIR=$(cat /mnt/hdd-storage/hexforge-content-engine/.latest-session-path 2>/dev/null)
BLOG_FILE="$SESSION_DIR/blog.md"
OUTPUT_DIR="/mnt/hdd-storage/hexforge-content-engine/output"

if [ -f "$BLOG_FILE" ]; then
  mkdir -p "$OUTPUT_DIR"
  PROJECT_NAME=$(basename "$(dirname "$SESSION_DIR")")
  PART_NAME=$(basename "$SESSION_DIR")
  cp "$BLOG_FILE" "$OUTPUT_DIR/${PROJECT_NAME}-${PART_NAME}.md"
  cp "$BLOG_FILE" "$OUTPUT_DIR/latest.md"
  echo "✅ Blog copied to: $OUTPUT_DIR/${PROJECT_NAME}-${PART_NAME}.md"
else
  echo "⚠️ blog.md not found in session directory."
fi

# Step 6: Generate TTS voiceover from the blog content
console.log("📢 Generating TTS voiceover...");
await execPromise('node ./scripts/generateVoiceFromBlog.js');
if [ $? -ne 0 ]; then
  echo "❌ TTS voiceover generation failed. Exiting."
  exit 1
fi

echo "🔊 Generating TTS voiceover..."

# ✅ Done
echo "✅ Linux-side blog pipeline completed!"
