import requests
import json
import random
import time
from datetime import datetime
import csv
import subprocess
import os
import shutil
import argparse
import graphviz
import re
import base64

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Loop Prompt Generator with ComfyUI")
parser.add_argument("--attempts", type=int, help="Override max attempts", default=None)
parser.add_argument("--min_score", type=float, help="Override minimum score", default=None)
parser.add_argument("--sleep", type=int, help="Seconds to wait after prompt", default=30)
parser.add_argument("--retry", type=int, help="Max retries for posting to ComfyUI", default=3)
parser.add_argument("--llm_model", type=str, help="LLM model to use (default: mistral)", default="mistral")
parser.add_argument("--use_llava", action="store_true", help="Enable LLaVA vision prompt refinement")
parser.add_argument("--template", type=str, help="Prompt template name override")
parser.add_argument("--no_guideline_repeat", action="store_true", help="Do not repeat prompt guidelines on refinement")
args = parser.parse_args()

# === Config ===
config = {
    "min_score": args.min_score if args.min_score is not None else 7.5,
    "max_attempts": args.attempts if args.attempts is not None else 10,
    "comfyui_url": "http://localhost:8188/prompt",
    "filename_prefix": "ai_control_room_loop",
    "project_name": "ai_control_room",
    "output_dir": "/mnt/hdd-storage/hexforge-content-engine/assets/ai_control_room/part1/images",
    "log_file": "/mnt/hdd-storage/hexforge-content-engine/assets/ai_control_room/part1/logs/image_scores.csv",
    "prompt_base": "AI control room with glowing monitors and command chairs, transparent interface panels, exposed wires and cooling ducts, cyberpunk style with cinematic lighting and ambient neon reflections, wide lens perspective.",
    "negative_prompt": "low resolution, deformed, blurry, missing screens, dull lighting, empty desk",
    "final_variants": 4,
    "sleep_after_prompt": args.sleep,
    "llm_model": args.llm_model,
    "use_llava": args.use_llava,
    "prompt_template_file": "prompt_templates.json",
    "prompt_guidelines_file": "prompt_guidelines.txt",
    "prompt_template_name": args.template or "default",
    "no_guideline_repeat": args.no_guideline_repeat
}

# Load prompt formatting guidelines from file
try:
    with open(config["prompt_guidelines_file"], "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.strip().lower().startswith("# template:"):
                config["prompt_template_name"] = line.strip().split(":", 1)[1].strip()
                print(f"[DEBUG] Auto-selected template from guidelines: {config['prompt_template_name']}")
        config["prompt_guidelines"] = ''.join(lines).strip()
        print("[DEBUG] Loaded prompt guidelines")
except Exception as e:
    print(f"[WARN] Could not load prompt guidelines: {e}")
    config["prompt_guidelines"] = ""

# Load optional prompt templates if present
TEMPLATES = {}
if os.path.exists(config["prompt_template_file"]):
    try:
        with open(config["prompt_template_file"], "r") as tf:
            TEMPLATES = json.load(tf)
            print(f"[DEBUG] Loaded prompt templates: {list(TEMPLATES.keys())}")
    except Exception as e:
        print(f"[WARN] Could not load prompt templates: {e}")

# === Template injection ===
def apply_prompt_template(template_name, description):
    if template_name in TEMPLATES:
        template = TEMPLATES[template_name]
        return template.replace("{{DESCRIPTION}}", description.strip())
    return description

# === Guidelines injection ===
def apply_guidelines(prompt, allow_repeat=True):
    if config.get("prompt_guidelines") and allow_repeat:
        return f"{config['prompt_guidelines'].strip()}\n\n{prompt.strip()}"
    return prompt

# === Apply both ===
def build_final_prompt(raw_prompt, template_name=None, allow_guidelines=True):
    templated = apply_prompt_template(template_name or config["prompt_template_name"], raw_prompt)
    return apply_guidelines(templated, allow_repeat=allow_guidelines and not config.get("no_guideline_repeat"))

# === Adjust truncation to allow longer prompt details ===
TRUNCATION_LIMITS = {
    "initial_prompt": (120, 500),
    "llava_description": (100, 400),
    "final_prompt": (100, 400),
    "shell_safe": (50, 200)
}

# === Negative prompt injector ===
def combine_prompts(main_prompt, negative_prompt):
    return f"Positive Prompt: {main_prompt}\nNegative Prompt: {negative_prompt}"

def clean_prompt_for_shell(text, max_words=None, max_chars=None):
    max_words = max_words or TRUNCATION_LIMITS["shell_safe"][0]
    max_chars = max_chars or TRUNCATION_LIMITS["shell_safe"][1]
    txt = re.sub(r"\(.*?\)", "", text)
    txt = txt.replace('"', '').replace('`', '').replace('$', '')
    txt = txt.replace('--', '—')
    txt = ' '.join(txt.split())
    txt = txt.rstrip('.,')
    words = txt.split()
    if len(words) > max_words:
        txt = ' '.join(words[:max_words])
        print(f"[WARN] Truncated to {max_words} words")
    if len(txt) > max_chars:
        txt = txt[:max_chars]
        print(f"[WARN] Truncated to {max_chars} chars")
    return txt

print(f"[DEBUG] Configuration: {json.dumps(config, indent=2)}")

# === Prompt Refinement Engine ===
run_log = {
    "best_score": 0,
    "best_prompt": config["prompt_base"],
    "best_image": None
}

def refine_prompt_with_llm(prev_prompt, score, attempt_num, preview_path, best_score=None):
    print(f"[DEBUG] Refining prompt on attempt #{attempt_num} with score {score:.2f}")
    if best_score is not None and score < best_score:
        print(f"[INFO] Current score {score:.2f} is less than best score {best_score:.2f}. Reusing best prompt.")
        prev_prompt = run_log["best_prompt"]
        preview_path = run_log.get("best_image", preview_path)
    if config["use_llava"] and os.path.exists(preview_path):
        try:
            print("[INFO] Using LLaVA for multimodal refinement")
            with open(preview_path, "rb") as f:
                image_bytes = f.read()
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "model": config["llm_model"],
                "prompt": (
                    f"You are a prompt optimization assistant. Based on this image and the original Stable Diffusion prompt, "
                    f"generate a stronger visual prompt to improve composition and aesthetics.\n\n"
                    f"Original Prompt: {prev_prompt}\n\nImproved Prompt:"
                ),
                "stream": False,
                "images": [encoded]
            }
            for i in range(3):
                try:
                    print(f"[DEBUG] Sending payload to LLaVA (attempt {i+1}) with image: {preview_path}")
                    response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
                    print("[DEBUG] LLaVA request completed.")
                    data = response.json()
                    suggestion = data.get("response") or data.get("text")
                    if suggestion:
                        print(f"[DEBUG] LLaVA returned suggestion: {suggestion[:300]}...")
                        return build_final_prompt(suggestion.strip(), allow_guidelines=False)
                except Exception as e:
                    print(f"[LLaVA ERROR] (attempt {i+1}) {e}")
                    time.sleep(3)
            print("[WARN] All LLaVA attempts failed. Falling back.")
        except Exception as e:
            print(f"[LLaVA ERROR] {e}")
    try:
        lprompt = (
            f"You are a prompt refinement model. Improve the following Stable Diffusion prompt by making it more descriptive, visual, and specific to increase CLIP and aesthetic scores.\n"
            f"Prompt: {prev_prompt}\nScore: {score:.2f}\n\nImproved Prompt:"
        )
        print(f"[DEBUG] Sending fallback refinement to LLM...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": config["llm_model"], "prompt": lprompt, "stream": False},
            timeout=120
        )
        print("[DEBUG] Fallback request completed.")
        data = response.json()
        suggestion = data.get("response") or data.get("text")
        if suggestion:
            print(f"[DEBUG] Fallback LLM suggestion: {suggestion[:300]}...")
            return build_final_prompt(suggestion.strip(), allow_guidelines=False)
    except Exception as e:
        print(f"[LLM ERROR] {e}")
    return build_final_prompt(prev_prompt, allow_guidelines=False)









# === Helpers ===
def clean_prompt_for_shell(text, max_words=50, max_chars=200):
    # Strip any parenthetical content
    txt = re.sub(r"\(.*?\)", "", text)
    # remove dangerous chars
    txt = txt.replace('"', '').replace('`', '').replace('$', '')
    # replace double-hyphens
    txt = txt.replace('--', '—')
    # collapse whitespace
    txt = ' '.join(txt.split())
    # remove trailing , and .
    txt = txt.rstrip('.,')
    # truncate by words
    words = txt.split()
    if len(words) > max_words:
        txt = ' '.join(words[:max_words])
        print(f"[WARN] Truncated to {max_words} words")
    # truncate by chars
    if len(txt) > max_chars:
        txt = txt[:max_chars]
        print(f"[WARN] Truncated to {max_chars} chars")
    return txt

# === ComfyUI Payload Builder ===
# (unchanged)

# === Main Loop & Scoring ===
# Integrate clean_prompt_for_shell() both when setting prompt_variant and in rate_generated_image()
# (rest of script remains the same)


# === ComfyUI Payload Builder ===
def build_prompt_json(prompt_text, neg_text, prefix):
    return {
        "prompt": {
            "0": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd15.ckpt"}},
            "1": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["0", 1], "text": prompt_text}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["0", 1], "text": neg_text}},
            "3": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1}},
            "4": {"class_type": "KSampler", "inputs": {
                "model": ["0", 0], "positive": ["1", 0], "negative": ["2", 0],
                "latent_image": ["3", 0],
                "steps": 25, "cfg": 7.5, "sampler_name": "euler", "scheduler": "normal", "denoise": 1,
                "seed": random.randint(0, 999999)
            }},
            "5": {"class_type": "VAEDecode", "inputs": {"samples": ["4", 0], "vae": ["0", 2]}},
            "6": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": prefix}}
        }
    }

# …rest of file unchanged…


def post_to_comfyui(prompt_json, retries=args.retry):
    for attempt in range(1, retries + 1):
        try:
            print(f"[DEBUG] Posting to ComfyUI (Attempt {attempt})")
            response = requests.post(config["comfyui_url"], headers={"Content-Type": "application/json"}, data=json.dumps(prompt_json))
            if response.ok:
                return True
        except Exception as e:
            print(f"[WARN] Attempt {attempt} failed: {e}")
        time.sleep(2)
    print("[ERROR] All retries failed. Retrying entire attempt in 5 seconds...")
    time.sleep(5)
    return post_to_comfyui(prompt_json, retries)

def rate_generated_image(filename, prompt):
    try:
        abs_path = os.path.abspath(filename)
        clean_prompt = clean_prompt_for_shell(prompt)
        result = subprocess.run([
            "./score_image_engine.sh", "--image", abs_path, "--prompt", clean_prompt, "--mode", "both"
        ], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        clip, aesthetic = data.get("clip_score", 0), data.get("aesthetic_score", 0)
        total = round((clip * 10 + aesthetic) / 2, 2)
        return total, clip, aesthetic
    except Exception as e:
        print(f"[Error scoring image] {e}")
        return 0, 0, 0

def log_result(filename, prompt, neg_prompt, total_score, clip, aesthetic):
    exists = os.path.isfile(config["log_file"])
    with open(config["log_file"], "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not exists:
            writer.writerow(["filename", "prompt", "negative_prompt", "score", "clip", "aesthetic", "timestamp"])
        writer.writerow([filename, prompt, neg_prompt, total_score, clip, aesthetic, datetime.now().isoformat()])

def draw_prompt_score_graph(attempts, output_path):
    dot = graphviz.Digraph(comment='Prompt Variants', format='png')
    for idx, att in enumerate(attempts):
        label = f"#{idx+1}: {att['total']}\n{att['prompt'][:40]}..."
        dot.node(str(idx), label=label)
        if idx > 0:
            dot.edge(str(idx-1), str(idx))
    dot.render(output_path, cleanup=True)

# === Main Loop ===
run_log = {
    "timestamp": datetime.now().isoformat(),
    "project": config["project_name"],
    "attempts": [],
    "accepted_prompt": None,
    "best_score": 0,
    "best_prompt": None,
    "best_image": None
}

base_prompt = config["prompt_base"]
negative_prompt = config["negative_prompt"]
best_score = 0
previous_prompt = base_prompt
last_score = 0
last_generated_path = None

for i in range(config["max_attempts"]):
    if i == 0:
        prompt_variant = base_prompt
    else:
        refined = refine_prompt_with_llm(previous_prompt, last_score, i, last_generated_path or "[NO IMAGE]")
        if refined.strip() == previous_prompt.strip():
            print("[WARN] LLM returned unchanged. Adding suffix for variation.")
            prompt_variant = f"{previous_prompt} [variant {i}]"
        else:
            prompt_variant = clean_prompt_for_shell(refined)

    file_prefix = f"{config['filename_prefix']}_{i:02d}"
    generated_file = f"output/{file_prefix}_00001_.png"
    payload = build_prompt_json(prompt_variant, negative_prompt, file_prefix)

    print(f"[Attempt {i+1}] Generating image: {prompt_variant}")
    if not post_to_comfyui(payload):
        print("[ERROR] ComfyUI post failed. Skipping.")
        continue

    time.sleep(config["sleep_after_prompt"])
    total, clip, aesthetic = rate_generated_image(generated_file, prompt_variant)
    print(f"[INFO] Score: {total} (CLIP: {clip}, Aesthetic: {aesthetic})")

    log_result(generated_file, prompt_variant, negative_prompt, total, clip, aesthetic)
    run_log["attempts"].append({"prompt": prompt_variant, "file": generated_file, "clip": clip, "aesthetic": aesthetic, "total": total})

    previous_prompt = prompt_variant
    last_score = total
    last_generated_path = generated_file

    if total > best_score:
        best_score = total
        run_log["best_score"] = total
        run_log["best_prompt"] = prompt_variant
        best_image = os.path.join(config["output_dir"], "best_prompt_result.png")
        shutil.copy(generated_file, best_image)
        run_log["best_image"] = best_image

    if total >= config["min_score"]:
        print(f"[INFO] Accepted prompt with score {total}.")
        break

run_log["accepted_prompt"] = run_log.get("best_prompt", base_prompt)
json_log = config["log_file"].replace(".csv", "_run.json")
with open(json_log, "w") as jf:
    json.dump(run_log, jf, indent=2)

preview = f"/mnt/hdd-storage/hexforge-content-engine/assets/{config['project_name']}/part1/preview.png"
shutil.copy(run_log.get("best_image"), preview)

draw_prompt_score_graph(run_log["attempts"], json_log.replace("_run.json", "_graph"))

print("[INFO] Generating final variants...")
for n in range(config["final_variants"]):
    fp = f"{config['filename_prefix']}_final_{n+1}"
    final_payload = build_prompt_json(run_log["best_prompt"], negative_prompt, fp)
    post_to_comfyui(final_payload)
    time.sleep(5)

print("[INFO] Loop Prompt Generator completed successfully.")
