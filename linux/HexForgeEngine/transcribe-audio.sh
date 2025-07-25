#!/bin/bash

# === HexForge Whisper Audio Transcriber ===
VENV_PATH="/mnt/hdd-storage/hexforge-content-engine/venv"
OUTPUT_DIR="/mnt/hdd-storage/hexforge-content-engine/blog_output"
WHISPER_LANG="English"

if [ -z "$1" ]; then
  echo "❌ Usage: $0 <input_audio_or_video>"
  exit 1
fi

INPUT="$1"
BASENAME=$(basename "$INPUT")
NAME="${BASENAME%.*}"
AUDIO_PATH="/tmp/${NAME}.wav"

source "$VENV_PATH/bin/activate"

if [[ "$INPUT" == *.mp4 || "$INPUT" == *.mkv || "$INPUT" == *.mov || "$INPUT" == *.webm ]]; then
  echo "🔄 Extracting audio from video..."
  ffmpeg -y -i "$INPUT" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$AUDIO_PATH"
else
  AUDIO_PATH="$INPUT"
fi

echo "🗣️ Transcribing..."
whisper "$AUDIO_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --language "$WHISPER_LANG" \
  --fp16 False

echo "✅ Done! Transcripts saved to: $OUTPUT_DIR"

if [[ "$AUDIO_PATH" == /tmp/*.wav && "$AUDIO_PATH" != "$INPUT" ]]; then
  rm "$AUDIO_PATH"
fi
