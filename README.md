# 🚀 HexForge Content Automation Engine

> Self-hosted AI pipeline to turn dev sessions into polished blogs, media, and narrated content.

---

## 🧠 What Is This?

**HexForge Content Engine** automates developer storytelling. It transforms screen recordings + CLI logs into:

* 📝 Blog posts (Markdown)
* 🎧 AI-narrated voiceovers
* 🎥 Avatar videos with synced lip animation
* 🖼️ Generated images using Stable Diffusion

---

## 🧭 Full Workflow Overview

📄 **Detailed Docs:** See [`docs/workflow.md`](docs/workflow.md)

```bash
1. Launch shell + OBS (Windows or Linux)
2. Capture logs, screen, and chat
3. Send to backend via SCP
4. Blog + voice auto-generated
5. Images rendered with prompt engine
6. Final assets zipped or uploaded
```

---

## 🧩 Modules & Docs

| Module                    | Description                                | Docs                                            |
| ------------------------- | ------------------------------------------ | ----------------------------------------------- |
| 🪟 **HexForgeRunner**     | PowerShell interface for OBS + CLI logging | [runner.md](docs/runner.md)                     |
| 🐧 **Linux Capture Node** | MX Linux logger and OBS mirror             | [linux-capture.md](docs/linux-capture.md)       |
| 🧠 **Backend Scripts**    | Blog, voice, and asset generation engine   | [scripts-overview.md](docs/scripts-overview.md) |
| 🎧 **Audio Engine**       | TTS narration and avatar sync              | [audio.md](docs/audio.md)                       |
| 🎥 **Video Engine**       | Subtitle + video rendering tools           | [video.md](docs/video.md)                       |
| 🎨 **Prompt Optimizer**   | Image scoring + refinement loop            | [prompt.md](docs/prompt.md)                     |
| 🖼️ **Image Engine**      | Stable Diffusion + ComfyUI integration     | [image.md](docs/image.md)                       |

---

## 🗂 Repo Layout

```bash
hexforge-content-engine/
├── docs/                  # Documentation per module
├── windows/HexForgeRunner/  # PowerShell scripts + assets
│   ├── assets/            # Screenshots, video, logs (empty in repo)
│   ├── projects/          # Session folders (empty in repo)
├── .gitignore
├── README.md              # You are here
```

---

## ✅ Status

* ✅ End-to-end blog + voice + image pipeline working
* ✅ Modular script system (Windows + Linux)
* ⚙️ Blog editor upload in progress
* 🧪 Prompt scoring loop running + saving variants
* 🔜 Final video assembler + dashboard planned

---

## 🔗 External Tools Used

* [OBS Studio](https://obsproject.com/)
* [SadTalker](https://github.com/OpenTalker/SadTalker)
* [Wav2Lip](https://github.com/Rudrabha/Wav2Lip)
* [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
* [LLaVA](https://llava-vl.github.io/)
* [Whisper](https://github.com/openai/whisper)
* [Mistral via Ollama](https://ollama.com/)

---

🔁 See [`docs/workflow.md`](docs/workflow.md) for full pipeline breakdown.
