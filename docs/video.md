# 🎥 HexForge Video Generation Engine – Dev Summary

*Last Updated: July 19, 2025*

---

## 🌟 Project Goal

Build a **modular AI-powered video generation system** that transforms blogs, scripts, or audio into narrated videos with optional avatars, subtitles, synced voice, and animated elements. This is one of the final stages of the full HexForge content automation pipeline.

---

## 🧩 Core Components

| Component                  | Role                                                                |
| -------------------------- | ------------------------------------------------------------------- |
| `generateVoiceFromBlog.js` | Converts blog Markdown or JSON into speech-ready narration text     |
| `SadTalker`                | Generates lip-synced avatar videos from voice audio + facial images |
| `Wav2Lip`                  | Syncs existing video or avatar renders with generated voice audio   |
| `tts_from_text.py`         | Converts narration text to `.wav` using local TTS engine            |
| `transcribe-audio.sh`      | (Reverse) Creates subtitles from finished voiceover                 |
| `validateAndAssemble.sh`   | (Planned) Final renderer for voice + image + subtitle composition   |

---

## 🛠️ Workflow Summary

1. **Narration Text** is generated via `generateVoiceFromBlog.js`
2. **Audio** is created via `tts_from_text.py` or TTS engine
3. **Avatar Render** (optional) via `SadTalker` or similar tools
4. **Voice Sync** applied using `Wav2Lip` if necessary
5. **Subtitles** are transcribed using `transcribe-audio.sh`
6. (Planned) Final video is stitched via `validateAndAssemble.sh`

---

## 📁 File Locations

### Base Scripts

`/mnt/hdd-storage/hexforge-content-engine/scripts/`

* Includes `generateVoiceFromBlog.js`, `transcribe-audio.sh`, `validateAndAssemble.sh`

### AI Tool Directory

`~/ai-tools/`

* `SadTalker/`, `Wav2Lip/`, `tts_from_text.py`

### Output

`/mnt/hdd-storage/hexforge-content-engine/assets/<project>/<part>/video/`

* All rendered video and audio output organized by project/part

---

## ✭ Related Tools

| Tool                       | Location               | Purpose                     |
| -------------------------- | ---------------------- | --------------------------- |
| `SadTalker`                | `~/ai-tools/SadTalker` | Avatar rendering + lip sync |
| `Wav2Lip`                  | `~/ai-tools/Wav2Lip`   | Audio/video sync correction |
| `tts_from_text.py`         | `ai-tools/`            | Main TTS generator          |
| `generateVoiceFromBlog.js` | `scripts/`             | Text-to-script conversion   |

---

## ✅ Status

* ✅ Blog to voice script working via `generateVoiceFromBlog.js`
* ✅ TTS audio generation works via local `tts_from_text.py`
* ✅ SadTalker + Wav2Lip tools installed
* ✅ Subtitles working via `transcribe-audio.sh`
* 🔹 Needs full integration and final stitching

---
