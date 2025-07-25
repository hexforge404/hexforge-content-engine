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
# [unchanged argument parsing]
# ...
args = parser.parse_args()

# === Config ===
config = {
    # [unchanged config setup]
}

# Ensure required folders exist
print(f"[DEBUG] Creating directories: {config['output_dir']} and {os.path.dirname(config['log_file'])}")
os.makedirs(config["output_dir"], exist_ok=True)
os.makedirs(os.path.dirname(config["log_file"]), exist_ok=True)

# === Removed Early Exit Check ===
# Removed premature check that exited before the loop ran

# === Prompt Refinement + Helper Functions ===
# [unchanged definitions for clean_prompt_for_shell, apply_guidelines, etc.]

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
            "6": {"class_type": "SaveImage", "inputs": {
                "images": ["5", 0],
                "filename_prefix": prefix,
                "output_path": config["output_dir"]
            }}
        }
    }

# === Main Multi-Seed Loop ===
seed_branches = []

for seed_num in range(config["max_seeds_total"]):
    print(f"\n=== Starting seed branch #{seed_num+1} ===")
    base_prompt = config["prompt_base"]
    prompt_history = []
    best_score = 0
    best_prompt = base_prompt
    best_image = None
    stale_count = 0

    for i in range(config["max_seed_refinements"]):
        prompt_variant = base_prompt if i == 0 else refine_prompt_with_llm(base_prompt, last_score, i, last_generated_path)
        prompt_variant = clean_prompt_for_shell(prompt_variant)
        file_prefix = f"{config['filename_prefix']}_s{seed_num+1}_r{i+1}"
        image_path = os.path.join(config["output_dir"], f"{file_prefix}_00001_.png")
        payload = build_prompt_json(prompt_variant, config["negative_prompt"], file_prefix)

        if not post_to_comfyui(payload):
            print("[ERROR] ComfyUI post failed. Skipping.")
            continue

        time.sleep(config["sleep_after_prompt"])
        total, clip, aesthetic = rate_generated_image(image_path, prompt_variant)
        print(f"[INFO] Score: {total} (CLIP: {clip}, Aesthetic: {aesthetic})")
        log_result(image_path, prompt_variant, config["negative_prompt"], total, clip, aesthetic)

        prompt_history.append({
            "prompt": prompt_variant,
            "image": image_path,
            "score": total,
            "clip": clip,
            "aesthetic": aesthetic
        })

        if total > best_score:
            best_score = total
            best_prompt = prompt_variant
            best_image = image_path
            stale_count = 0
        else:
            stale_count += 1
            if stale_count >= config["max_stale"]:
                print(f"[INFO] Seed {seed_num+1} stagnated. Stopping early.")
                break

        base_prompt = prompt_variant
        last_score = total
        last_generated_path = image_path

    seed_branches.append({
        "seed_num": seed_num + 1,
        "best_score": best_score,
        "best_prompt": best_prompt,
        "best_image": best_image,
        "attempts": prompt_history
    })

# === Post-Loop Validation Moved Here ===
valid_seeds = [s for s in seed_branches if s.get("best_image") and os.path.exists(s["best_image"])]
if not valid_seeds:
    print("[ERROR] No valid images were generated. Exiting.")
    exit(1)

# === Select Top Scoring Seed ===
top_seed = max(valid_seeds, key=lambda s: s["best_score"])
# [copy preview, save run_log, etc. — unchanged]


# Copy preview and best images safely
print(f"[DEBUG] Checking top_seed best_image existence...")
top_seed = {"best_image": None, "best_prompt": None, "best_score": 0}  # placeholder for debug
if top_seed.get("best_image") and os.path.exists(top_seed["best_image"]):
    print(f"[DEBUG] Copying best image from: {top_seed['best_image']}")
    shutil.copy(top_seed["best_image"], preview_img)
    shutil.copy(top_seed["best_image"], best_img)
else:
    print("[WARN] No valid best image found to copy.")

# Optional: Validate seeds before continuing
seed_branches = []  # placeholder for debug
valid_seeds = [s for s in seed_branches if s.get("best_image") and os.path.exists(s["best_image"])]
print(f"[DEBUG] Found {len(valid_seeds)} valid seed(s) with images.")
if not valid_seeds:
    print("[ERROR] No valid images were generated. Exiting.")
    exit(1)

top_seed = max(valid_seeds, key=lambda s: s["best_score"])
print(f"[INFO] Best prompt: {top_seed['best_prompt']} with score {top_seed['best_score']}")





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


# === ComfyUI Payload Builder patch ===
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
            "6": {"class_type": "SaveImage", "inputs": {
                "images": ["5", 0],
                "filename_prefix": prefix,
                "output_path": config["output_dir"]  # ✅ Force output path
            }}
        }
    }


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

# === Multi-seed Planning ===
seed_branches = []

for seed_num in range(config["max_seeds_total"]):
    print(f"\n=== Starting seed branch #{seed_num+1} ===")
    base_prompt = config["prompt_base"]
    prompt_history = []
    best_score = 0
    best_prompt = base_prompt
    best_image = None
    stale_count = 0

    for i in range(config["max_seed_refinements"]):
        prompt_variant = base_prompt if i == 0 else refine_prompt_with_llm(base_prompt, last_score, i, last_generated_path)
        prompt_variant = clean_prompt_for_shell(prompt_variant)
        file_prefix = f"{config['filename_prefix']}_s{seed_num+1}_r{i+1}"
        image_path = os.path.join(config["output_dir"], f"{file_prefix}_00001_.png")
        payload = build_prompt_json(prompt_variant, config["negative_prompt"], file_prefix)

        if not post_to_comfyui(payload):
            print("[ERROR] ComfyUI post failed. Skipping.")
            continue

        time.sleep(config["sleep_after_prompt"])
        total, clip, aesthetic = rate_generated_image(image_path, prompt_variant)
        print(f"[INFO] Score: {total} (CLIP: {clip}, Aesthetic: {aesthetic})")
        log_result(image_path, prompt_variant, config["negative_prompt"], total, clip, aesthetic)

        prompt_history.append({
            "prompt": prompt_variant,
            "image": image_path,
            "score": total,
            "clip": clip,
            "aesthetic": aesthetic
        })

        if total > best_score:
            best_score = total
            best_prompt = prompt_variant
            best_image = image_path
            stale_count = 0
        else:
            stale_count += 1
            if stale_count >= config["max_stale"]:
                print(f"[INFO] Seed {seed_num+1} stagnated. Stopping early.")
                break

        base_prompt = prompt_variant
        last_score = total
        last_generated_path = image_path

    seed_branches.append({
        "seed_num": seed_num + 1,
        "best_score": best_score,
        "best_prompt": best_prompt,
        "best_image": best_image,
        "attempts": prompt_history
    })

# Select top scoring seed
print("\n[INFO] Selecting best scoring seed...")
top_seed = max(seed_branches, key=lambda s: s["best_score"])
print(f"[INFO] Best prompt: {top_seed['best_prompt']} with score {top_seed['best_score']}")

# Save run log
run_log_path = config["log_file"].replace(".csv", "_multi_seed_run.json")
with open(run_log_path, "w") as jf:
    json.dump({"seeds": seed_branches, "best": top_seed}, jf, indent=2)

# Generate preview and best copy
preview_img = os.path.join(config["output_dir"], "preview.png")
best_img = os.path.join(config["output_dir"], "best_prompt_result.png")
if os.path.exists(top_seed["best_image"]):
    shutil.copy(top_seed["best_image"], preview_img)
    shutil.copy(top_seed["best_image"], best_img)

# Generate visual graph
draw_prompt_score_graph(top_seed["attempts"], run_log_path.replace(".json", "_graph"))

# Generate final variants
print("[INFO] Generating final variants...")
for n in range(config["final_variants"]):
    fp = f"{config['filename_prefix']}_final_{n+1}"
    final_payload = build_prompt_json(top_seed["best_prompt"], config["negative_prompt"], fp)
    post_to_comfyui(final_payload)
    time.sleep(5)

print("[INFO] Loop Prompt Generator completed successfully.")
