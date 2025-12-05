#!/usr/bin/env python3
import argparse
import json
import os
import random
import time

import requests

BASE_DIR = "/mnt/hdd-storage/hexforge-content-engine"
COMFY_URL = "http://localhost:8188/prompt"


def build_prompt_json(prompt_text: str, neg_text: str, output_dir: str, prefix: str) -> dict:
    """Minimal ComfyUI workflow: SD1.5 + SaveImage to the given output_dir."""
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
                "inputs": {"width": 768, "height": 512, "batch_size": 1},
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
                    "seed": random.randint(0, 999999),
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
                    "output_path": output_dir,
                },
            },
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Simple ComfyUI runner for HexForge Content Engine")
    parser.add_argument("--project", required=True)
    parser.add_argument("--part", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--num-images", type=int, default=2)
    args = parser.parse_args()

    output_dir = os.path.join(BASE_DIR, "assets", args.project, args.part, "images")
    os.makedirs(output_dir, exist_ok=True)

    negative_prompt = "low quality, blurry, distorted, watermark, text, noisy, artifacts"

    print(f"[simple-runner] Project={args.project} Part={args.part}")
    print(f"[simple-runner] Output dir: {output_dir}")
    print(f"[simple-runner] Prompt: {args.prompt!r}, num_images={args.num_images}")

    for i in range(args.num_images):
        prefix = f"{args.project}_{args.part}_n{i+1}"
        payload = build_prompt_json(args.prompt, negative_prompt, output_dir, prefix)

        print(f"[simple-runner] Posting {i+1}/{args.num_images} to ComfyUI with prefix={prefix} ...")
        try:
            resp = requests.post(COMFY_URL, json=payload, timeout=120)
            resp.raise_for_status()
        except Exception as e:
            print(f"[simple-runner][ERROR] ComfyUI request failed: {e}")
            return 1

        # small delay so ComfyUI can write the file
        time.sleep(3)

    print("[simple-runner] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
