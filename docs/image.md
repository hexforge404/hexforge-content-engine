# 🖼️ HexForge Image Engine – Dev Summary

*Last Updated: July 21, 2025*

---

## ✨ Project Goal

Design a modular AI-driven **image generation and refinement engine** using ComfyUI, integrated into the HexForge Content Automation Engine. This module generates image assets for blog posts, thumbnails, or creative visuals based on AI prompts extracted from dev session logs.

---

## 🔧 Core Components

| Component                  | Role                                                     |
| -------------------------- | -------------------------------------------------------- |
| `loop_prompt_generator.py` | Multi-seed image prompt runner and refinement controller |
| `ComfyUI`                  | Node-based GUI engine for image generation               |
| `LLaVA`                    | Image scoring and feedback for refinement loop           |
| `hexforge_prompt_runner/`  | Directory containing prompt runner modules and templates |
| `prompt-log.json`          | Log file with scores and generated prompt/image metadata |
| `final-variants/`          | Stores top 4 images with best score                      |

---

## 📂 Directory Structure

**Root:** `/mnt/hdd-storage/hexforge-content-engine/`

```
hexforge_prompt_runner/
├── loop_prompt_generator.py
├── templates/
│   └── blog_image_template.json
├── prompt-log.json
├── output/
│   ├── all-seeds/
│   └── final-variants/
```

---

## ♻️ Workflow Summary

1. `loop_prompt_generator.py` receives blog metadata or logs
2. Prompts injected into a ComfyUI JSON template
3. Images generated in batches using multiple seeds
4. `LLaVA` scores each result by quality and relevance
5. Loop continues until best score meets threshold
6. Final 4 images exported to `final-variants/`

---

## ✨ Features

* Multi-seed and multi-iteration prompt injection
* Auto-export of top-scoring variants
* Scoring graph + metadata saved to `prompt-log.json`
* Uses `ComfyUI` with predefined graph templates
* Optional manual rerun with prior settings

---

## 🔹 Status

* ✅ Prompt runner functional with multiple seeds and iterations
* ✅ Score feedback loop from LLaVA integrated
* ✅ ComfyUI batch mode working with JSON injection
* ✅ Logs and final variants exported cleanly
* ⚠️ Auto-regeneration based on score needs polish
* ✅ Ready for integration with `generateBlogFromJSON.js`

---

## 🔗 Related Tools

| Tool                       | Role                                 |
| -------------------------- | ------------------------------------ |
| `generateBlogFromJSON.js`  | Source of blog prompts from logs     |
| `loop_prompt_generator.py` | Main loop for refinement and scoring |
| `ComfyUI`                  | Image generation engine              |
| `LLaVA`                    | Image scoring + guidance loop        |
