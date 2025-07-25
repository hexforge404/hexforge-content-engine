#!/bin/bash

# 📁 Directory to watch for incoming ZIP files from the Windows-side uploader
WATCH_DIR="/mnt/hdd-storage/hexforge-content-engine/uploads/windows"

# 📂 Base destination directory for project-based unpacking
DEST_BASE="/mnt/hdd-storage/hexforge-content-engine/Assets"

# ⏱️ Polling interval to check for new files (in seconds)
INTERVAL=10

# 🧠 File to track already-processed ZIPs to prevent duplicate processing
PROCESSED_LIST="/tmp/processed_hexforge_zips.txt"
touch "$PROCESSED_LIST"

echo "🔄 Watching for new ZIP files in: $WATCH_DIR"

while true; do
  for zipfile in "$WATCH_DIR"/*.zip; do
    [ -e "$zipfile" ] || continue

    if grep -Fxq "$zipfile" "$PROCESSED_LIST"; then
      echo "🔁 Skipping already processed ZIP: $(basename "$zipfile")"
      continue
    fi

    echo "📦 Found new ZIP: $(basename "$zipfile")"

    # 🧠 Extract project and part from zip filename: format must be projectname_partname.zip
    zipname=$(basename "$zipfile")
    project=$(echo "$zipname" | cut -d'_' -f1)
    part=$(echo "$zipname" | cut -d'_' -f2 | cut -d'.' -f1)

    if [[ -z "$project" || -z "$part" ]]; then
      echo "❌ Could not extract project/part from filename. Skipping."
      continue
    fi

    echo "🧩 Project: $project"
    echo "🧩 Part: $part"

    dest_dir="$DEST_BASE/$project/$part"
    echo "📁 Destination path: $dest_dir"
    mkdir -p "$dest_dir"

    echo "📂 Unzipping into: $dest_dir"
    unzip -o "$zipfile" -d "$dest_dir" > /dev/null
    if [ $? -eq 0 ]; then
      echo "✅ Successfully unzipped: $(basename "$zipfile")"
    else
      echo "❌ Failed to unzip: $(basename "$zipfile")"
      continue
    fi

    echo "📝 Copying logs to central log archive..."
    find "$dest_dir" -iname "*.log" -exec cp {} /mnt/hdd-storage/hexforge-content-engine/logs/HexForge_Content_Engine/ \;

    echo "🎞️ Copying videos to main video directory..."
    find "$dest_dir" -iname "*.mkv" -exec cp {} /mnt/hdd-storage/Videos/HexForge/ \;

    echo "$zipfile" >> "$PROCESSED_LIST"
    echo "✅ Unpacked and processed: $zipfile"
  done

  echo "⏳ Sleeping for $INTERVAL seconds..."
  sleep "$INTERVAL"
done
