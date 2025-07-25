import os
import time
import shutil
import json
import argparse
from datetime import datetime
from .refinement import refine_prompt_with_llm
from .helpers import (
    clean_prompt_for_shell,
    post_to_comfyui,
    rate_generated_image,
    log_result,
    draw_prompt_score_graph
)
from .payloads import build_prompt_json

def wait_for_image(image_path, timeout=60):
    print(f"[WAIT] Waiting for image to appear: {image_path}")
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(image_path):
            return True
        time.sleep(1)
    print(f"[ERROR] File not found after timeout: {image_path}")
    return False

def run_prompt_loop(config):
    required_keys = [
        "project_name", "output_dir", "log_file", "prompt_base", "negative_prompt",
        "filename_prefix", "max_seeds_total", "max_seed_refinements", "sleep_after_prompt",
        "max_stale", "final_variants"
    ]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    seed_branches = []
    run_log_base = {
        "timestamp": datetime.now().isoformat(),
        "project": config["project_name"],
        "seeds": []
    }

    os.makedirs(config["output_dir"], exist_ok=True)
    os.makedirs(os.path.dirname(config["log_file"]), exist_ok=True)

    for seed_num in range(config["max_seeds_total"]):
        print(f"\n=== Starting seed branch #{seed_num+1} ===")
        base_prompt = config["prompt_base"]
        prompt_history = []
        best_score = 0
        best_prompt = base_prompt
        best_image = None
        stale_count = 0
        last_score = 0
        last_generated_path = None

        for i in range(config["max_seed_refinements"]):
            if i == 0 or not last_generated_path or not os.path.exists(last_generated_path):
                prompt_variant = base_prompt
            else:
                prompt_variant = refine_prompt_with_llm(
                    base_prompt, last_score, i, last_generated_path, config, {
                        "best_prompt": best_prompt,
                        "best_image": best_image,
                        "best_score": best_score
                    })

            prompt_variant = clean_prompt_for_shell(prompt_variant)

            file_prefix = f"{config['filename_prefix']}_s{seed_num+1}_r{i+1}"
            image_path = os.path.join(
                config["output_dir"], f"{file_prefix}_00001_.png")
            payload = build_prompt_json(
                prompt_variant, config["negative_prompt"], file_prefix, config)

            if not post_to_comfyui(payload, config=config):
                print("[ERROR] ComfyUI post failed. Skipping.")
                continue

            if not wait_for_image(image_path):
                continue

            time.sleep(config["sleep_after_prompt"])
            total, clip, aesthetic = rate_generated_image(
                image_path, prompt_variant, config)
            print(f"[INFO] Score: {total} (CLIP: {clip}, Aesthetic: {aesthetic})")

            log_result(image_path, prompt_variant, config["negative_prompt"],
                       total, clip, aesthetic, config=config)

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

    valid_seeds = [s for s in seed_branches if s.get("best_image") and os.path.exists(s["best_image"])]
    if not valid_seeds:
        print("[ERROR] No valid images were generated. Exiting.")
        exit(1)

    top_seed = max(valid_seeds, key=lambda s: s["best_score"])
    print(f"[INFO] Best prompt: {top_seed['best_prompt']} with score {top_seed['best_score']}")

    run_log_path = config["log_file"].replace(".csv", "_multi_seed_run.json")
    with open(run_log_path, "w") as jf:
        json.dump({"seeds": seed_branches, "best": top_seed}, jf, indent=2)

    preview_img = os.path.join(config["output_dir"], "preview.png")
    best_img = os.path.join(config["output_dir"], "best_prompt_result.png")
    if os.path.exists(top_seed["best_image"]):
        shutil.copy(top_seed["best_image"], preview_img)
        shutil.copy(top_seed["best_image"], best_img)

    draw_prompt_score_graph(top_seed["attempts"], run_log_path.replace(".json", "_graph"))

    print("[INFO] Generating final variants...")
    for n in range(config["final_variants"]):
        fp = f"{config['filename_prefix']}_final_{n+1}"
        final_payload = build_prompt_json(
            top_seed["best_prompt"], config["negative_prompt"], fp, config)
        post_to_comfyui(final_payload, config=config)
        time.sleep(5)

    print("[✅] Loop Prompt Generator completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HexForge Prompt Runner CLI")
    parser.add_argument("--config_file", type=str, help="Path to JSON config file", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        raise FileNotFoundError(f"Config file not found: {args.config_file}")

    with open(args.config_file, "r") as cf:
        config = json.load(cf)

    run_prompt_loop(config)
    print("[INFO] Starting HexForge Prompt Runner...")