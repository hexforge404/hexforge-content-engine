#!/bin/bash

# Activate venv if needed
source /mnt/hdd-storage/hexforge-content-engine/venv/bin/activate

# Run the Python scoring script
python /mnt/hdd-storage/hexforge-content-engine/scripts/score_image.py "$@" 2>&1
if [ $? -ne 0 ]; then
  echo "❌ Scoring failed. Check the logs for details."
  exit 1
fi  
echo "✅ Scoring completed successfully."
