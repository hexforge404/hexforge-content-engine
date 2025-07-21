# 🎵 HexForge Audio Engine – Dev Summary

*Last Updated: July 19, 2025*

---

## 🌟 Project Goal

Build a **modular, AI-driven audio generation and processing engine** for use in the HexForge Content Automation system. This engine handles transcription, voice synthesis, and alignment with generated visuals (via SadTalker + Wav2Lip), creating clean voiceover audio or narrated content from raw logs and blog markdown.

---

## 🔧 Core Components

| Component                  | Role                                                          |
| -------------------------- | ------------------------------------------------------------- |
| `transcribe-audio.sh`      | Extracts and transcribes voice from videos using Whisper      |
| `generateVoiceFromBlog.js` | Generates TTS audio based on blog markdown using SadTalker    |
| `SadTalker`                | Produces animated avatar video with voice and facial sync     |
| `Wav2Lip`                  | Enhances lip-sync on faces using the voice file               |
| `voice-script.md`          | Script file generated from blog, input for TTS                |
| `tts_from_text.py`         | Wrapper used by SadTalker to render voice audio from markdown |

## 🌐 Directory Layout

### Engine Base

`/mnt/hdd-storage/hexforge-content-engine/scripts/`

* Includes `transcribe-audio.sh`, `generateVoiceFromBlog.js`, and other blog/audio tools

### AI Tools Location

`~/ai-tools/`

* Installed via `install-hexforge-ai-tools.sh`
* Includes:

  * `SadTalker`
  * `Wav2Lip`
  * `stable-diffusion-webui`

### Inputs/Outputs

| Path                                         | Purpose                                |
| -------------------------------------------- | -------------------------------------- |
| `input/blog.json`                            | Contains title, slug, and blog content |
| `voice-script.md`                            | Cleaned markdown input for TTS         |
| `output/blog-project-part-3b.wav`            | Final audio output per blog post       |
| `output/blog-project-part-3b.mp4` (optional) | Optional video output from SadTalker   |

## 🔎 Voice Generation Flow

1. `voice-script.md` is generated from blog JSON
2. `tts_from_text.py` renders `.wav` file using SadTalker
3. (Optional) SadTalker avatar video or Wav2Lip sync generated
4. Audio saved to `/output/` with blog slug and part name

## 💡 Features

* Whisper-based transcription for raw video
* Markdown-to-voice via SadTalker
* Modular wrapper (`tts_from_text.py`) for TTS
* Optional face animation/sync using SadTalker or Wav2Lip
* Integrates directly with content engine pipeline

## ✨ Status

* ✅ Voiceover from blog fully functional
* ✅ Transcription from input video tested with Whisper
* ✅ SadTalker installed and rendering
* ✅ Wav2Lip downloaded and used for test sync
* ✅ Files routed to `/output/` cleanly
