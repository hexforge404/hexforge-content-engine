# 📜 Scripts & Folder Structure – HexForge Backend

*Last Updated: July 21, 2025*

---

## 📁 Key Directory Layout

This section documents the backend directory structure and core scripts used by the HexForge Content Automation Engine hosted on the Proxmox server. All paths assume the base directory:

```
/mnt/hdd-storage/hexforge-content-engine/
```

---

## 🗂️ Base Folders

| Folder                    | Description                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------- |
| `scripts/`                | Primary shell + Node.js scripts for processing, blog generation, and uploads                      |
| `assets/`                 | Session output: blogs, videos, audio, screenshots, etc. Structured as `/assets/<project>/<part>/` |
| `logs/`                   | CLI logs and system logs from each run                                                            |
| `input/`                  | Holds `blog.json` input files and preprocessed data                                               |
| `output/`                 | Final output of blog text, audio, and associated metadata                                         |
| `uploads/`                | SCP dropzone for incoming zip bundles from Windows/Linux                                          |
| `hexforge_prompt_runner/` | Prompt loop engine for image generation (with scoring + refinements)                              |

---

## ⚙️ Core Scripts

### Top-Level Pipeline

| Script                   | Purpose                                                                           |
| ------------------------ | --------------------------------------------------------------------------------- |
| `runFullPipeline.sh`     | Master script for full blog generation pipeline (log/video → blog/audio/image)    |
| `watchAndProcessZips.sh` | Watches the `uploads/` folder for incoming sessions and unzips + invokes pipeline |

### Blog & Audio Generation

| Script                       | Purpose                                                                |
| ---------------------------- | ---------------------------------------------------------------------- |
| `buildBlogJsonFromAssets.js` | Extracts logs/video to build a valid blog.json input file              |
| `generateBlogFromJSON.js`    | Converts blog.json to full markdown blog post                          |
| `generateVoiceFromBlog.js`   | Converts blog text into TTS narration script                           |
| `tts_from_text.py`           | Runs SadTalker/voice engine to generate `.wav` narration from markdown |

### Uploading & Automation

| Script                   | Purpose                                                                         |
| ------------------------ | ------------------------------------------------------------------------------- |
| `bulkUploadBlogs.js`     | Uploads multiple blog markdown files to HexForge blog API                       |
| `transcribe-audio.sh`    | Transcribes voice files back into text (for subtitles or alignment)             |
| `validateAndAssemble.sh` | (Planned) Merge final blog, voice, visuals, and metadata into distributable zip |

---

## 🧪 Development Tools

These support prompt refinement, Stable Diffusion image scoring, and visual asset prep:

| Tool/Script                   | Role                                                                      |
| ----------------------------- | ------------------------------------------------------------------------- |
| `score_image.py`              | LLaVA-powered scoring of SD-generated images for selection                |
| `install-a1111-as-devuser.sh` | Auto-installs Stable Diffusion + ComfyUI for `devuser` account on Proxmox |

---

## 🔗 Related Docs

* [🧠 Backend Overview](backend.md)
* [🎥 Video Engine](video.md)
* [🖼️ Prompt Engine](prompt.md)
