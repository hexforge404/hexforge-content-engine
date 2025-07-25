📄 README.md – Loop Prompt Generator (HexForge Prompt Runner)
markdown
Copy
Edit
# HexForge Prompt Runner

🧠 **AI-Powered Prompt Optimization Loop** using:
- 🖼️ Stable Diffusion via **ComfyUI**
- 🧪 Prompt refinement via **LLM (e.g., Mistral or LLaVA)**
- 🎯 CLIP + Aesthetic scoring via local scripts
- 📊 Multi-seed loop logic with auto-pruning and final variant generation

---

## 📦 Project Structure

hexforge-prompt-runner/
├── cli.py # Argument parser (flags like --retry, --sleep)
├── config.py # Central config dictionary
├── helpers.py # Logging, scoring, graphing, retry logic
├── payloads.py # Builds ComfyUI payloads
├── refinement.py # Handles LLaVA or fallback LLM-based prompt refinement
├── main.py # Entry point for the full loop
├── templates/
│ ├── prompt_templates.json # (Optional) Format rules
│ └── prompt_guidelines.txt # (Optional) Guidelines

yaml
Copy
Edit

---

## 🚀 How to Run

### ▶️ Prerequisites

- Python 3.10+
- ComfyUI running on `http://localhost:8188`
- Local scoring script: `score_image_engine.sh` in root
- Ollama / LLaVA running at `http://localhost:11434` (if using multimodal)

### 🔧 Install Python requirements

```bash
pip install -r requirements.txt
▶️ Run the Loop Generator
bash
Copy
Edit
python main.py --retry 3 --sleep 30 --min_score 7.5
Available Flags (from cli.py)

Flag	Description
--retry	Retry attempts for ComfyUI posts (default: 3)
--sleep	Delay (seconds) after each image is sent to ComfyUI
--min_score	Minimum score threshold for selecting best prompts
--use_llava	Use LLaVA multimodal image feedback (default: True)

🧠 How It Works
Base prompt is refined in loop using LLaVA or fallback LLM.

Each variant is scored with local score_image_engine.sh.

Best-scoring prompts are retained across seed branches.

A visual prompt graph and final variants are generated.

preview.png and best_prompt_result.png are saved to output.

📁 Outputs
Saved under config["output_dir"] (e.g., /mnt/hdd-storage/...):

*_00001_.png – images per iteration

preview.png – latest best result

best_prompt_result.png – final best

image_scores.csv – scoring log

*_graph.png – visual prompt evolution graph

*_multi_seed_run.json – full metadata log

📌 Notes
You can customize prompt_base and negative_prompt in config.py.

Guidelines and templates are optional, but help provide prompt consistency.

The script works best with a local Ollama instance for fast LLM feedback.

🛠️ Future Features (Planned)
GUI version using PyQt or TUI

Batch blog/image pairing with the HexForge Content Engine

Support for other scoring models (e.g., BLIP)

© 2025 HexForge Labs — All Rights Reserved

yaml
Copy
Edit

---

Let me know if you want this saved as an actual file now (`README.md`) or if you'd like a VS Code task/alias to run it easily.






