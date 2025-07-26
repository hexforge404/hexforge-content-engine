# 📄 HexForge Content Engine – Backend (Proxmox/Linux)

*Last Updated: July 21, 2025*

---

## 🧠 Overview

The backend engine powers the transformation of captured development sessions into structured, publishable content using AI models and local scripts. It is hosted on a Proxmox server and communicates with the Windows-side HexForgeRunner via SCP.

## 📍 Directory Location

```
/mnt/hdd-storage/hexforge-content-engine
```

## 📁 Directory Structure

| Folder                    | Purpose                                                   |
| ------------------------- | --------------------------------------------------------- |
| `scripts/`                | All shell/JS/Python tools for blog/audio/image generation |
| `assets/`                 | Final generated blog content, audio, images               |
| `logs/`                   | CLI session logs and run logs                             |
| `input/`                  | blog.json and other inputs built by Windows runner        |
| `output/`                 | Final blog text, `.wav`, `.md`, `.json`, etc.             |
| `uploads/`                | SCP drop point from Windows                               |
| `hexforge_prompt_runner/` | Visual prompt loop w/ scoring + LLaVA feedback            |

## 🧰 Key Scripts

| Script                       | Purpose                                        |
| ---------------------------- | ---------------------------------------------- |
| `runFullPipeline.sh`         | Launches the entire processing chain           |
| `generateBlogFromJSON.js`    | Converts blog.json to markdown blog            |
| `buildBlogJsonFromAssets.js` | Extracts metadata and session info from assets |
| `generateVoiceFromBlog.js`   | Builds TTS-ready voice script from blog        |
| `tts_from_text.py`           | Calls SadTalker to generate `.wav`             |
| `transcribe-audio.sh`        | Whisper-based audio transcription              |
| `score_image.py`             | Scores images for prompt ranking               |
| `validateAndAssemble.sh`     | Planned tool to stitch audio/video/images      |

## 🧪 Toolchain Overview

| Tool                 | Role                                       |
| -------------------- | ------------------------------------------ |
| **Ollama (Mistral)** | Blog and metadata generation               |
| **SadTalker**        | TTS + facial animation (optional video)    |
| **Wav2Lip**          | Voice-video lip sync refinement            |
| **ComfyUI**          | Image prompt loop and generation engine    |
| **LLaVA**            | Image scoring and prompt optimization loop |

## 🔁 Workflow Summary

1. Assets sent to `uploads/` from Windows runner
2. `watchAndProcessZips.sh` detects and unpacks
3. `buildBlogJsonFromAssets.js` generates `blog.json`
4. `generateBlogFromJSON.js` creates `.md` post
5. `tts_from_text.py` creates `.wav` narration
6. `SadTalker` and `Wav2Lip` optionally create video
7. `ComfyUI` prompt loop generates and ranks images
8. Everything is saved to `assets/<project>/<part>/`

## ✅ Current Status

* ✅ Full blog pipeline functional (logs → markdown)
* ✅ Voiceover works via SadTalker
* ✅ Audio sync and scoring loops operational
* ✅ Windows SCP drop works cleanly
* ✅ Prompt generator and multi-seed loop tested
* ⏳ `validateAndAssemble.sh` pending full integration

---

Return to [📄 HexForgeRunner →](runner.md)
