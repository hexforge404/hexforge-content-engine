#!/usr/bin/env python3
"""
simple_comfy_runner.py

Entry point for the HexForge Content Engine → ComfyUI bridge.

Modes:
  - simple:   fire a single ComfyUI generation for the given prompt
  - opt:      call loop_prompt_generator.py to run multi-image scoring
              with optional LLM refinement (Ollama)
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
import json
import random

BASE = Path("/mnt/hdd-storage/hexforge-content-engine")
ASSETS_BASE = BASE / "assets"

COMFY_ROOT = Path("/root/ai-tools/ComfyUI")
COMFY_OUTPUT_ROOT = COMFY_ROOT / "output"
COMFY_URL = os.getenv("COMFY_URL", "http://localhost:8188/prompt")

# Optimizer script (the loop_prompt_generator you just updated)
OPTIMIZER_SCRIPT = (
    BASE / "linux" / "HexForgeEngine" / "scripts" / "loop_prompt_generator.py"
)

# Simple negative prompt (can keep in sync with optimizer if desired)
NEGATIVE_PROMPT = (
    "low detail, out of focus, boring background, distorted anatomy, "
    "plastic look, missing electronics, blurry textures"
)


def build_simple_prompt_json(prompt_text: str, neg_text: str, prefix: str, output_subdir: str) -> dict:
    """
    A minimal one-shot ComfyUI graph, same shape as the optimizer’s.
    """
    return {
        "prompt": {
            "0": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "sd15.ckpt"},
            },
            "1": {
                "class_type": "CLIPTextEncode",
                "inputs": {"clip": ["0", 1], "text": prompt_text},
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {"clip": ["0", 1], "text": neg_text},
            },
            "3": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 768, "height": 768, "batch_size": 1},
            },
            "4": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["0", 0],
                    "positive": ["1", 0],
                    "negative": ["2", 0],
                    "latent_image": ["3", 0],
                    "steps": 25,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "seed": random.randint(0, 999_999),
                },
            },
            "5": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["4", 0], "vae": ["0", 2]},
            },
            "6": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["5", 0],
                    "filename_prefix": prefix,
                    "output_path": output_subdir,
                },
            },
        }
    }


def post_to_comfyui(payload: dict, retries: int = 3) -> bool:
    for attempt in range(1, retries + 1):
        try:
            print(f"[runner] Posting to ComfyUI (attempt {attempt})")
            import requests  # local import

            resp = requests.post(COMFY_URL, json=payload, timeout=120)
            if resp.ok:
                return True
            print(f"[runner] ComfyUI error: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"[runner] ComfyUI request failed: {e}")
        time.sleep(2)
    print("[runner] All ComfyUI attempts failed.")
    return False


def wait_for_image(out_dir: Path, prefix: str, timeout: int = 180) -> Path | None:
    target = out_dir / f"{prefix}_00001_.png"
    print(f"[runner] Waiting for image: {target}")
    start = time.time()
    while time.time() - start < timeout:
        if target.exists():
            print("[runner] Image found.")
            return target
        time.sleep(2)
    print("[runner] Timed out waiting for image.")
    return None


def run_simple(project: str, part: str, prompt: str) -> int:
    """
    Single-shot generation: one image into assets/<project>/<part>/images.
    """
    output_dir = ASSETS_BASE / project / part / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    comfy_subdir = f"simple/{project}/{part}"
    comfy_out_dir = COMFY_OUTPUT_ROOT / comfy_subdir
    comfy_out_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"{project}_{part}_simple"
    print(f"[runner] Simple mode")
    print(f"[runner] Project={project} Part={part}")
    print(f"[runner] Engine assets dir = {output_dir}")
    print(f"[runner] Comfy output dir = {comfy_out_dir}")
    print(f"[runner] Prompt = {prompt!r}")

    payload = build_simple_prompt_json(prompt, NEGATIVE_PROMPT, prefix, comfy_subdir)

    if not post_to_comfyui(payload):
        print("[runner] Aborting simple mode due to ComfyUI failure.")
        return 1

    img_path = wait_for_image(comfy_out_dir, prefix)
    if not img_path:
        print("[runner] No image produced in simple mode.")
        return 1

    # Copy to assets
    final_path = output_dir / "simple.png"
    print(f"[runner] Copying simple result to {final_path}")
    final_path.write_bytes(img_path.read_bytes())

    # Save prompt text alongside
    (output_dir / "simple_prompt.txt").write_text(prompt, encoding="utf-8")

    print("[runner] Simple mode done.")
    return 0


def run_optimizer(
    project: str,
    part: str,
    prompt: str,
    num_images: int,
) -> int:
    """
    Call loop_prompt_generator.py with optional LLM refinement toggles
    controlled via environment or CLI.
    """
    if not OPTIMIZER_SCRIPT.exists():
        print(f"[runner] Optimizer script not found: {OPTIMIZER_SCRIPT}")
        return 1

    # Env toggles
    use_refiner_env = os.getenv("HEXFORGE_USE_REFINER", "").lower()
    use_refiner = use_refiner_env in ("1", "true", "yes")

    refiner_model = os.getenv("HEXFORGE_REFINER_MODEL", "mistral")
    refiner_variants_env = os.getenv("HEXFORGE_REFINER_VARIANTS", "3")
    try:
        refiner_variants = max(1, int(refiner_variants_env))
    except ValueError:
        refiner_variants = 3

    cmd = [
        sys.executable,
        str(OPTIMIZER_SCRIPT),
        "--project",
        project,
        "--part",
        part,
        "--prompt",
        prompt,
        "--num-images",
        str(num_images),
    ]

    if use_refiner:
        cmd.extend(
            [
                "--use-refiner",
                "--refiner-model",
                refiner_model,
                "--refiner-variants",
                str(refiner_variants),
            ]
        )

    print("[runner] Optimizer mode")
    print(f"[runner] Project={project} Part={part}")
    print(f"[runner] Prompt={prompt!r}")
    print(f"[runner] Num images={num_images}")
    print(f"[runner] Use refiner={use_refiner}")
    if use_refiner:
        print(
            f"[runner] Refiner model={refiner_model} variants={refiner_variants}"
        )
    print(f"[runner] Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"[runner] Optimizer subprocess failed: {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HexForge ComfyUI runner (simple or optimizer mode)"
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--part", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--mode",
        choices=["simple", "opt"],
        default="simple",
        help="simple = single image, opt = multi-image optimizer",
    )
    parser.add_argument(
        "--num-images",
        type=int,
        default=3,
        help="Number of images/variants in optimizer mode (ignored for simple).",
    )

    args = parser.parse_args()

    if args.mode == "simple":
        return run_simple(args.project, args.part, args.prompt)
    else:
        return run_optimizer(args.project, args.part, args.prompt, args.num_images)


if __name__ == "__main__":
    raise SystemExit(main())
