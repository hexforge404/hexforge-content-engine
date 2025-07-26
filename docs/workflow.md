# 🔁 Workflow Overview – HexForge Content Engine

*Last Updated: July 21, 2025*

---

## 🧭 Full Pipeline Flow

This document outlines the end-to-end workflow for the HexForge Content Automation Engine — from capture to publish.

---

### 🪟 Step 1: Windows Capture via HexForgeRunner

Run from your main dev box:

1. Launch HexForgeRunner PowerShell menu
2. Start OBS recording + CLI logging
3. Work through development session
4. End session → script auto-packages assets to `.zip`
5. SCP to Proxmox `/uploads/`

📁 **Assets collected:** `logs`, `screenshots`, `video.mp4`, `chat.md`

---

### 📥 Step 2: Uploads Processed on Proxmox

Proxmox backend watches `uploads/` for new session `.zip` files:

1. `watchAndProcessZips.sh` unpacks to `assets/<project>/<part>/`
2. `buildBlogJsonFromAssets.js` creates structured `blog.json`
3. Logs + transcripts are embedded

✅ **Result:** Ready-to-process structured input per session

---

### 🧠 Step 3: Blog + Audio Generation

1. `generateBlogFromJSON.js` creates full blog post (`.md`)
2. `generateVoiceFromBlog.js` builds narration script
3. `tts_from_text.py` renders final `.wav` voiceover

📁 Output saved in `/output/` and `/assets/<project>/<part>/`

---

### 🎥 Step 4: Video + Subtitle Rendering (Optional)

1. `SadTalker` avatar render or `Wav2Lip` sync
2. `transcribe-audio.sh` creates `.srt` subtitles
3. `validateAndAssemble.sh` (planned) joins video, voice, blog, meta

---

### 🖼️ Step 5: Prompt Loop + Visual Generation

1. `hexforge_prompt_runner/loop_prompt_generator.py` runs multi-seed loop
2. Stable Diffusion + ComfyUI generate images
3. `score_image.py` (LLaVA) evaluates results
4. Best images saved to `/assets/<project>/<part>/`

📊 Scores logged + plotted

---

### 📤 Step 6: Publish

* `bulkUploadBlogs.js` pushes `.md` blog posts to site
* All associated assets can be zipped + archived

---

## 🔗 Related Docs

* [Runner Module](runner.md)
* [Backend Structure](scripts-overview.md)
* [Audio Engine](audio.md)
* [Prompt Engine](prompt.md)
* [Video Engine](video.md)
