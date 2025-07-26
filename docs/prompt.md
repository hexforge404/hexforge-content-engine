# 🔍 HexForge Prompt Optimizer Engine

*Last Updated: July 19, 2025*

---

## 🌟 Project Goal

Develop a **self-hosted AI-powered visual content generator** that refines image prompts using Stable Diffusion + ComfyUI with auto-iteration, scoring, and final variant export. This engine feeds into the full HexForge content automation pipeline.

---

## 🗉️ Core Engine Components

| Component                  | Role                                                              |
| -------------------------- | ----------------------------------------------------------------- |
| `loop_prompt_generator.py` | Core Python script that loops, scores, and selects best image set |
| `run-generator.sh`         | Shell wrapper to run loop script with safe defaults               |
| `score_image.py`           | Evaluates output images based on preset prompt criteria           |
| `ComfyUI workflows`        | JSON templates injected or preloaded for image generation         |
| `prompt_templates.json`    | Prompt examples and guidance for generation loop                  |
| `comfyui.log`              | Logging output for generation and scoring runs                    |

---

## 🛠️ Current Workflow

1. Launch `run-generator.sh` with desired flags
2. Loop generates multiple image sets (multi-seed)
3. Each image scored with `score_image.py`
4. Top scoring seed prompt is saved and used to generate final 4 variants
5. Outputs saved in:

   ```
   /mnt/hdd-storage/hexforge-content-engine/assets/<project>/<part>/images
   ```

## 🥺 Prompt Evaluation Flags

| Flag                     | Description                                            |
| ------------------------ | ------------------------------------------------------ |
| `--use_llava`            | Enables multi-modal scoring w/ LLaVA model             |
| `--max_seeds_total`      | Total seeds to generate and score                      |
| `--max_seed_refinements` | Reruns per seed before discarding                      |
| `--min_score`            | Score threshold for continuing loop                    |
| `--sleep`                | Delay between attempts (comfy rate limit)              |
| `--retry`                | Number of attempts before fallback on failure          |
| `--final_variant_mode`   | Mode used for last image set: best\_prompt, best\_seed |

---

## 📁 Directory Layout

### Engine Base

```
/mnt/hdd-storage/hexforge-content-engine/scripts/
```

* All core scripts like `runFullPipeline.sh`, `generateBlogFromJSON.js`, `score_image.py`

### ComfyUI Installation

```
~/ai-tools/ComfyUI/
```

* Installed via `install-hexforge-ai-tools.sh`
* Contains `models/`, `workflows/`, `scripts/run-loop-multi-seed.sh`

### Final Outputs

```
/mnt/hdd-storage/hexforge-content-engine/assets/<project>/<part>/images/
```

* Includes both scored drafts and final 4 best variants

---

## 🔗 Related Tools

| Tool/Dir                   | Location                         | Purpose                                      |
| -------------------------- | -------------------------------- | -------------------------------------------- |
| `ComfyUI`                  | `~/ai-tools/ComfyUI/`            | Stable Diffusion UI and image generator      |
| `loop_prompt_generator.py` | `scripts/` within content engine | Main looping script for prompt refinement    |
| `score_image_engine.sh`    | `scripts/`                       | Image evaluation logic via LLaVA or criteria |
| `run-loop-multi-seed.sh`   | `ComfyUI/scripts/`               | Alt shell runner for multi-seed refinements  |
| `SadTalker`, `Wav2Lip`     | `~/ai-tools/`                    | Used in later stages for video voice sync    |

---

## ✅ Status

* ✅ Prompt loop functional (multi-seed, scoring, final export)
* ✅ Scripts wired into blog pipeline
* ✅ All outputs consistently routed to `assets/`
* ✅ JSON prompt injection into ComfyUI workflows tested and saved

---

## 🚀 Planned Improvements

* [ ] Add GUI toggle for best\_prompt vs best\_seed mode
* [ ] Expand prompt template generator for blog topics
* [ ] Sync variant image sets with blog JSON post metadata
* [ ] Route all scores and attempts to timeline logs for visual debugging
* [ ] Add optional LLaVA reranker step on top 3 seeds before final export
