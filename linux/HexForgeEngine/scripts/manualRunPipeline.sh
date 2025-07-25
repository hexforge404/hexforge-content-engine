#!/bin/bash

# File: scripts/manualRunPipeline.sh
# Description: Manually run the blog pipeline by selecting a specific ZIP file, unzipping, and processing through the pipeline

INPUT_DIR="/mnt/hdd-storage/hexforge-content-engine/uploads/windows"
PIPELINE_DIR="/mnt/hdd-storage/hexforge-content-engine/scripts"
TMP_UNZIP_DIR="/mnt/hdd-storage/hexforge-content-engine/uploads/tmp"

mkdir -p "$TMP_UNZIP_DIR"

# Step 1: Scan for zip files and prompt user to select one
zip_files=($(find "$INPUT_DIR" -maxdepth 1 -name '*.zip'))

if [ ${#zip_files[@]} -eq 0 ]; then
  echo "❌ No .zip files found in: $INPUT_DIR"
  exit 1
fi

echo "📦 Available ZIP Content Packs:"
for i in "${!zip_files[@]}"; do
  echo "[$i] $(basename \"${zip_files[$i]}\")"
done

echo
read -p "🔍 Select a ZIP by number (or type 'exit'): " index
[[ "$index" == "exit" ]] && exit 0

selected_zip="${zip_files[$index]}"
echo "📂 Selected: $(basename \"$selected_zip\")"

# Step 1.5: Extract project and part name from ZIP filename
zip_filename=$(basename "$selected_zip")
project_name=$(echo "$zip_filename" | awk -F'_Part' '{print $1}' | sed 's/HexForge_Pack_//')
part_name=$(echo "$zip_filename" | grep -o 'Part[^_]*')
echo "📛 Project: $project_name"
echo "🧩 Part: $part_name"

# Step 2: Extract the ZIP
unzip_dir="$TMP_UNZIP_DIR/$(basename "$selected_zip" .zip)"
echo "📦 Unzipping to: $unzip_dir"
rm -rf "$unzip_dir"
unzip -q "$selected_zip" -d "$unzip_dir"

# Step 3: Confirm and begin running each stage of the pipeline
read -p "⚠️ Proceed to run blog pipeline on extracted content? (y/n): " confirm
[[ "$confirm" != "y" ]] && exit 0

# Stage 1: Build blog JSON using all available assets
echo "🚀 [Stage 1] Running buildBlogJsonFromAssets.js on: $unzip_dir"
node "$PIPELINE_DIR/buildBlogJsonFromAssets.js" "$unzip_dir"
echo

# Stage 2: Find video and run screen OCR
video_file=$(find "$unzip_dir" -type f -name '*.mkv' | head -n 1)
if [ -z "$video_file" ]; then
  echo "⚠️ [Stage 2] No .mkv video found in folder. Skipping OCR."
else
  echo "🎥 [Stage 2] Found video: $video_file"
  echo "🧠 [Stage 2] Running extractScreenTextFromVideo.js on: $(basename \"$video_file\")"
  node "$PIPELINE_DIR/extractScreenTextFromVideo.js" "$video_file"
  echo
fi

# Stage 3: Generate draft blog content from AI using gathered data
echo "📝 [Stage 3] Running generateDraftFromAI.js..."
node "$PIPELINE_DIR/generateDraftFromAI.js"
echo

# Final output message
echo "✅ Pipeline finished for: $(basename \"$selected_zip\")"
