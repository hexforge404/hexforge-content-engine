[📄 View HexForgeRunner documentation →](docs/runner.md)

**HexForgeRunner** is a PowerShell-based content automation tool designed for developers and creators who want to capture dev sessions, screen recordings, and terminal logs, then send them to a remote AI engine for blog and media generation.

Built as part of the **HexForge Content Automation Engine**, this Windows-side toolkit launches OBS, tracks your session, collects logs and video, and packages everything for upload and processing.

## ✨ Key Features

* Launches labeled shell sessions with logging
* Integrates with OBS Studio for screen recording
* Monitors OBS to auto-stop capture
* Builds JSON blog metadata from session logs
* Sends session data to a remote engine via SCP
* Reusable project and part naming system
* Automated folder structure and asset management

## 🧰 Tech Stack

* PowerShell 5+ (Windows)
* OBS Studio
* SCP (OpenSSH or PuTTY)
* Remote Linux server with AI processing engine

---

[📄 View Backend Engine documentation →](docs/backend.md)

*Last Updated: July 18, 2025*

## 🧠 Overview

The HexForge Content Automation Engine is a multi-part AI-powered pipeline that transforms screen-recorded development sessions into structured blogs, media packs, and Notion content blocks. The system includes:

* A dual-platform recording and packaging frontend (Windows + Linux)
* A processing backend hosted on Proxmox with AI toolchain integration
* Scripts for video + log ingestion, blog generation, voice narration, and asset export

## 💻 Platform Components

### 🪟 Windows Capture Interface

* **Location:** `C:\Users\kon-boot\Documents\WindowsPowerShell\Modules\HexForgeRunner\`
* **Core Features:**

  * OBS recording launcher
  * CLI session logging (via `hexforge-shell.ps1`)
  * Packager (`pack-and-send.ps1`) with SCP transfer to Proxmox
  * Clipboard-to-chat saver (WIP)

### 🐧 Linux Capture Node

* **Host:** MX Linux (`hex-sandbox`)
* **Tools Installed:** OBS, CLI logger, Flatpak support
* **Status:** Wired into the content pipeline and operational

[📄 View Proxmox Backend details →](docs/backend.md#proxmox-backend-engine)

**Root Directory:** `/mnt/hdd-storage/hexforge-content-engine`

### 📁 Key Directories

| Folder                    | Purpose                                                    |
| ------------------------- | ---------------------------------------------------------- |
| `scripts/`                | Blog generation, AI prompt pipelines, scoring, uploading   |
| `assets/`                 | Generated output: images, voice, logs, final markdown      |
| `logs/`                   | Session logs from CLI or pipeline run                      |
| `input/`                  | Input JSONs created by CLI or `buildBlogJsonFromAssets.js` |
| `output/`                 | Final rendered blog text, audio, and metadata              |
| `uploads/`                | SCP-drop folder for incoming session archives              |
| `hexforge_prompt_runner/` | AI prompt loop, multi-seed logic, LLaVA scoring            |

### 📜 Scripts Extracted

* `runFullPipeline.sh` – Full pipeline launcher (blog, voice, asset gen)
* `transcribe-audio.sh` – Audio-to-text processor for narration
* `bulkUploadBlogs.js` – Upload multiple blog markdown files to API
* `generateBlogFromJSON.js` – Converts blog.json to full markdown
* `buildBlogJsonFromAssets.js` – Constructs input JSON from logs/videos
* `score_image.py` – Image quality scoring module (used in prompt loop)
* `validateAndAssemble.sh` – Final merge and cleanup
* `install-a1111-as-devuser.sh` – Installer for Stable Diffusion GUI

## 🧠 Toolchain Summary

| Tool/Model                | Role                                          |
| ------------------------- | --------------------------------------------- |
| `Ollama` (Mistral)        | AI for blog/narration text generation         |
| `SadTalker` + `TTSTalker` | Text-to-speech voice output                   |
| `Wav2Lip`                 | Lip-sync voice to video avatar                |
| `ComfyUI`                 | Image generation and prompt loop runner       |
| `LLaVA`                   | Image scorer + feedback loop in prompt runner |

## 🔁 Workflow Summary

1. **Session Start:** OBS + CLI logger launched (Windows or Linux)
2. **Session End:** Assets zipped and sent to `/uploads/` via SCP
3. **Extraction & Pairing:** `watchAndProcessZips.sh` unpacks session and invokes pipeline
4. **Blog Build:** `buildBlogJsonFromAssets.js` → `generateBlogFromJSON.js`
5. **Voice Gen:** `generateVoiceFromBlog.js` → `SadTalker` or `TTS`
6. **Asset Assembly:** Images scored, merged, voice and blog exported
7. **Post Upload:** Markdown uploaded via `bulkUploadBlogs.js` or saved locally

## 🧩 Current Status

* ✅ Windows-side HexForgeRunner fully operational
* ✅ Linux MX sandbox wired into capture and CLI logging
* ✅ Pipeline end-to-end works from log/video to blog/audio
* ⚠️ Image refinement loop (prompt runner) in progress
* 🔄 Blog editor integration with `/api/blog` to be finalized

---
