#!/usr/bin/env python3
import argparse
import csv
import json
import math
import os
import random
import shutil
import subprocess
import time
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict

# ================================================================
# Paths & config
# ================================================================
BASE = Path("/mnt/hdd-storage/hexforge-content-engine")
ASSETS_BASE = BASE / "assets"
LOGS_BASE = BASE / "logs" / "comfy-jobs"

COMFY_ROOT = Path("/root/ai-tools/ComfyUI")
COMFY_OUTPUT_ROOT = COMFY_ROOT / "output"

# ComfyUI HTTP prompt endpoint
COMFY_URL = os.getenv("COMFY_URL", "http://localhost:8188/prompt")

# Local Ollama model for refinement
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Negative prompt (from your homelab_hero workflow)
DEFAULT_NEGATIVE_PROMPT = (
    "low detail, out of focus, boring background, distorted anatomy, "
    "plastic look, missing electronics, blurry textures"
)

# Script that scores images (CLIP + aesthetic)
SCORE_SCRIPT = BASE / "score_image_engine.sh"

# Stagnation control for early stopping
MAX_STAGNANT_ROUNDS = int(os.getenv("HEXFORGE_MAX_STAGNANT", "2"))

# Where blog draft JSON lives (for injection)
BLOG_OUTPUT_DIR = BASE / "linux" / "HexForgeEngine" / "output"
BLOG_DRAFT_PATH = BLOG_OUTPUT_DIR / "blog-draft.json"


# ================================================================
# ComfyUI helpers (base URL + queue control)
# ================================================================
def get_comfy_base_url() -> str:
    """
    Strip the /prompt suffix off COMFY_URL so we can talk to other endpoints
    like /queue/clear without hardcoding the host/port twice.
    """
    return COMFY_URL.rsplit("/", 1)[0]


def clear_comfy_queue(context: str = "") -> None:
    """
    Try to clear the ComfyUI queue so the optimizer job runs on a clean slate.
    This is best-effort: failures are logged but never crash the run.
    """
    try:
        import requests  # type: ignore

        base = get_comfy_base_url()
        url = base + "/queue/clear"
        label = f" ({context})" if context else ""
        print(f"[loop] Clearing ComfyUI queue{label} via {url}")
        resp = requests.post(url, timeout=10)
        if not resp.ok:
            print(
                f"[loop] Warning: queue clear HTTP {resp.status_code}: "
                f"{resp.text[:200]}"
            )
        else:
            print("[loop] ComfyUI queue cleared.")
    except Exception as e:
        print(f"[loop] Could not clear ComfyUI queue: {e}")


# ================================================================
# ComfyUI graph builder
# ================================================================
def build_prompt_json(
    prompt_text: str, neg_text: str, prefix: str, output_subdir: str
) -> dict:
    """
    Minimal SD1.5 graph mirroring homelab_hero style workflow.
    Image is saved to COMFY_OUTPUT_ROOT / output_subdir as {prefix}_00001_.png
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
                    # Force absolute output path so we always know where files land
                    "output_path": str(COMFY_OUTPUT_ROOT / output_subdir),
                },
            },
        }
    }


def post_to_comfyui(payload: dict, retries: int = 3) -> bool:
    for attempt in range(1, retries + 1):
        try:
            print(f"[loop] Posting to ComfyUI (attempt {attempt})")
            import requests  # type: ignore

            resp = requests.post(COMFY_URL, json=payload, timeout=120)
            if resp.ok:
                return True
            print(f"[loop] ComfyUI HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[loop] ComfyUI request failed: {e}")
        time.sleep(2)
    print("[loop] All ComfyUI attempts failed.")
    return False


# ================================================================
# Robust image wait helper
# ================================================================
def wait_for_image(prefix: str, timeout: int = 300) -> Optional[Path]:
    """
    Wait for an image whose filename CONTAINS `prefix` to appear
    anywhere under COMFY_OUTPUT_ROOT (recursively).

    - Searches the whole tree under /root/ai-tools/ComfyUI/output
    - Picks the *newest* match by mtime
    - Logs what it finds
    """
    print(
        f"[loop] Waiting for image with prefix '{prefix}' "
        f"anywhere under {COMFY_OUTPUT_ROOT}"
    )
    start = time.time()

    # 🔍 One-time debug: show all PNGs Comfy currently has
    print("[debug] Existing PNGs in output tree:")
    try:
        count = 0
        for p in COMFY_OUTPUT_ROOT.rglob("*.png"):
            print("   ", p)
            count += 1
        print(f"[debug] PNG count: {count}")
    except Exception as e:
        print(f"[debug] Error listing existing PNGs: {e}")

    while time.time() - start < timeout:
        try:
            matches: List[Path] = []
            for p in COMFY_OUTPUT_ROOT.rglob("*.png"):
                if prefix in p.name:
                    matches.append(p)

            if matches:
                # Pick newest by modification time
                best = max(matches, key=lambda p: p.stat().st_mtime)
                print(f"[loop] Found candidate image: {best}")
                return best
        except Exception as e:
            # rglob or stat failure shouldn't kill the loop
            print(f"[loop] Error while scanning for images: {e}")

        time.sleep(2)

    print("[loop] Timed out waiting for image.")
    return None


# ================================================================
# Scoring
# ================================================================
def score_image(img_path: Path, prompt: str) -> Tuple[float, float, float]:
    """
    Use score_image_engine.sh to compute CLIP + aesthetic scores.
    Returns (total_score, clip_score, aesthetic_score).

    NOTE: if score_image_engine.sh fails or returns non-JSON, this
    falls back to (0.0, 0.0, 0.0), which is why you sometimes see
    scores of exactly 0.0 across the board.
    """
    try:
        cmd = [
            str(SCORE_SCRIPT),
            "--image",
            str(img_path),
            "--prompt",
            prompt,
            "--mode",
            "both",
        ]
        print(f"[loop] Scoring image: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        clip = float(data.get("clip_score", 0))
        aesth = float(data.get("aesthetic_score", 0))
        total = round((clip * 10 + aesth) / 2, 2)
        return total, clip, aesth
    except Exception as e:
        print(f"[loop] Error scoring image {img_path}: {e}")
        return 0.0, 0.0, 0.0


def log_score(csv_path: Path, row: List):
    """
    Append a score row to CSV. Fully guarded so logging never kills the run.
    """
    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        exists = csv_path.exists()
        with csv_path.open("a", newline="") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(
                    [
                        "round",
                        "variant",
                        "filename",
                        "prompt",
                        "negative_prompt",
                        "score",
                        "clip",
                        "aesthetic",
                        "timestamp",
                    ]
                )
            writer.writerow(row)
    except Exception as e:
        print(f"[optimizer] Failed to write score log: {e}")


# ================================================================
# Prompt refinement via Ollama (positive + negative)
# ================================================================
def refine_prompts_via_ollama(
    base_positive: str,
    base_negative: str,
    best_score: float,
    clip_score: float,
    aesth_score: float,
    round_index: int,
) -> Tuple[str, str]:
    """
    Ask the local Ollama model to slightly refine BOTH positive and negative
    prompts based on scores. Returns (new_positive, new_negative).
    If anything fails, the originals are returned unchanged.
    """
    if not OLLAMA_URL:
        print("[loop] OLLAMA_URL not set; skipping refinement.")
        return base_positive, base_negative

    try:
        import requests  # type: ignore

        url = OLLAMA_URL.rstrip("/") + "/api/chat"
        system_msg = (
            "You refine visual art prompts for Stable Diffusion style models. "
            "You must refine BOTH a positive and a negative prompt. "
            "Make small, precise improvements only. "
            "Keep each under 80 words. "
            "Return STRICT JSON with keys 'positive' and 'negative' and nothing else."
        )
        user_msg = (
            f"Current prompts for round {round_index}.\n\n"
            f"Scores: total={best_score}, clip={clip_score}, aesthetic={aesth_score}.\n\n"
            f"Positive prompt:\n{base_positive}\n\n"
            f"Negative prompt:\n{base_negative}\n\n"
            "Refine BOTH prompts to be clearer and more vivid while preserving the same concept. "
            "Return ONLY JSON like:\n"
            '{"positive": "...", "negative": "..."}'
        )
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            "stream": False,
        }
        print(f"[loop] Calling Ollama at {url} model={OLLAMA_MODEL}")
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {}).get("content") or ""
        msg = msg.strip()
        if not msg:
            print("[loop] Empty refinement result; keeping original prompts.")
            return base_positive, base_negative

        # Expect JSON from the model
        try:
            parsed = json.loads(msg)
            new_pos = parsed.get("positive") or base_positive
            new_neg = parsed.get("negative") or base_negative
            print(f"[loop] Refined positive:\n{new_pos}")
            print(f"[loop] Refined negative:\n{new_neg}")
            return new_pos.strip(), new_neg.strip()
        except Exception as e:
            print(f"[loop] Failed to parse JSON refinement: {e}. Raw:\n{msg}")
            return base_positive, base_negative

    except Exception as e:
        print(f"[loop] Ollama refinement failed: {e}")
        return base_positive, base_negative


# ================================================================
# Grid composite for quick visual comparison
# ================================================================
def make_grid(images: List[Path], out_path: Path, cols: int = 3):
    """
    Build a simple N-image grid (3xN by default). If Pillow is missing,
    this safely no-ops.
    """
    if not images:
        return

    try:
        from PIL import Image  # type: ignore
    except Exception as e:
        print(f"[loop] Pillow not installed; skipping grid composite: {e}")
        return

    try:
        # Open all images
        opened = [Image.open(str(p)).convert("RGB") for p in images]
        w, h = opened[0].size

        cols = max(1, cols)
        rows = math.ceil(len(opened) / cols)

        grid_w = cols * w
        grid_h = rows * h

        grid = Image.new("RGB", (grid_w, grid_h))
        for idx, img in enumerate(opened):
            r = idx // cols
            c = idx % cols
            grid.paste(img, (c * w, r * h))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        grid.save(str(out_path))
        print(f"[loop] Grid composite saved to {out_path}")
    except Exception as e:
        print(f"[loop] Failed to build grid composite: {e}")


# ================================================================
# Blog injection helper
# ================================================================
def inject_best_into_blog_draft(
    project: str, part: str, summary: Dict, base_path: Path
) -> None:
    """
    Inject best image + scores into blog-draft.json so the blog pipeline
    can pick it up. This never raises; failures are logged only.
    """
    try:
        BLOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if BLOG_DRAFT_PATH.exists():
            with BLOG_DRAFT_PATH.open("r", encoding="utf-8") as f:
                draft = json.load(f)
        else:
            draft = {}

        optimizer = draft.setdefault("imageOptimizer", {})
        key = f"{project}_{part}"

        # Make path relative to BASE so JS side can resolve cleanly
        best_image_abs = Path(summary["best_image"]).resolve()
        try:
            rel_best = os.path.relpath(best_image_abs, start=base_path)
        except Exception:
            rel_best = str(best_image_abs)

        optimizer[key] = {
            "project": project,
            "part": part,
            "bestImage": rel_best,
            "bestScore": summary["best_score"],
            "bestPrompt": summary["best_prompt"],
            "generatedAt": summary["generated_at"],
        }

        # Optionally set heroImage if not already set
        hero = draft.setdefault("heroImage", {})
        hero.setdefault("src", rel_best)
        hero.setdefault(
            "alt", f"AI generated artwork for {project} {part}"
        )

        with BLOG_DRAFT_PATH.open("w", encoding="utf-8") as f:
            json.dump(draft, f, indent=2)
        print(f"[loop] Injected best image into blog draft at {BLOG_DRAFT_PATH}")

    except Exception as e:
        print(f"[loop] Failed to inject into blog draft: {e}")


# ================================================================
# Main optimization loop
# ================================================================
def main() -> int:
    parser = argparse.ArgumentParser(
        description="HexForge prompt optimizer w/ multi-round refinement"
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--part", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--num-images",
        type=int,
        default=3,
        help="Variants per round (from watcher/job file)",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=int(os.getenv("HEXFORGE_MAX_ROUNDS", "3")),
        help="Maximum refinement rounds",
    )
    parser.add_argument(
        "--target-score",
        type=float,
        default=float(os.getenv("HEXFORGE_TARGET_SCORE", "7.5")),
        help="Stop early if best total score >= this value",
    )
    args = parser.parse_args()

    project = args.project
    part = args.part
    current_positive = args.prompt
    current_negative = DEFAULT_NEGATIVE_PROMPT
    variants_per_round = max(1, args.num_images)
    max_rounds = max(1, args.max_rounds)
    target_score = args.target_score

    # Final engine assets dir
    assets_dir = ASSETS_BASE / project / part / "images"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Make sure logs directory exists
    LOGS_BASE.mkdir(parents=True, exist_ok=True)

    scores_csv = LOGS_BASE / f"{project}_{part}_optimizer_scores.csv"
    summary_json = LOGS_BASE / f"{project}_{part}_optimizer_summary.json"

    base_subdir = f"optimizer/{project}/{part}"

    print(f"[loop] Project={project} Part={part}")
    print(f"[loop] Assets dir = {assets_dir}")
    print(f"[loop] Scores CSV = {scores_csv}")
    print(f"[loop] Variants/round = {variants_per_round}")
    print(f"[loop] Max rounds = {max_rounds}, Target score = {target_score}")
    print(f"[loop] Starting positive prompt:\n{current_positive}")
    print(f"[loop] Starting negative prompt:\n{current_negative}")

    # 🔧 Clear ComfyUI queue at start so we don't mix with old jobs
    clear_comfy_queue(context="before optimizer job")

    best_global_score = -1.0
    best_global_image: Optional[Path] = None
    best_global_prompt = current_positive

    no_improve_rounds = 0
    manifest_entries: List[Dict] = []

    for r in range(1, max_rounds + 1):
        print(f"\n[loop] ===== Round {r}/{max_rounds} =====")
        round_best_score = -1.0
        round_best_image: Optional[Path] = None

        prev_best_global = best_global_score

        # Comfy output subdir for this round
        round_subdir = f"{base_subdir}/r{r}"
        comfy_round_dir = COMFY_OUTPUT_ROOT / round_subdir
        comfy_round_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, variants_per_round + 1):
            prefix = f"{project}_{part}_r{r}_v{i}"
            print(f"\n[loop] --- Variant {i}/{variants_per_round}, prefix={prefix} ---")

            payload = build_prompt_json(
                current_positive,
                current_negative,
                prefix,
                round_subdir,
            )

            if not post_to_comfyui(payload):
                print("[loop] Skipping variant due to ComfyUI failure.")
                continue

            img_path = wait_for_image(prefix)
            if not img_path:
                print("[loop] No image produced for this variant.")
                continue

            total, clip, aesth = score_image(img_path, current_positive)
            print(f"[loop] Score = {total} (CLIP={clip}, Aesthetic={aesth})")

            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

            log_score(
                scores_csv,
                [
                    r,
                    i,
                    str(img_path),
                    current_positive,
                    current_negative,
                    total,
                    clip,
                    aesth,
                    timestamp,
                ],
            )

            manifest_entries.append(
                {
                    "round": r,
                    "variant": i,
                    "filename": str(img_path),
                    "prompt": current_positive,
                    "negative_prompt": current_negative,
                    "score": total,
                    "clip": clip,
                    "aesthetic": aesth,
                    "timestamp": timestamp,
                }
            )

            if total > round_best_score:
                round_best_score = total
                round_best_image = img_path

            if total > best_global_score:
                best_global_score = total
                best_global_image = img_path
                best_global_prompt = current_positive

        if round_best_image is None:
            print(f"[loop] Round {r}: no successful variants.")
        else:
            print(
                f"[loop] Round {r} best = {round_best_image} "
                f"(score={round_best_score})"
            )

        # Early stop if we already hit the target
        if best_global_score >= target_score:
            print(
                f"[loop] Target score reached (best={best_global_score} >= {target_score}); stopping."
            )
            break

        # Check for stagnation (no global improvement this round)
        if best_global_score <= prev_best_global:
            no_improve_rounds += 1
            print(
                f"[loop] No global improvement this round "
                f"(stagnant rounds = {no_improve_rounds}/{MAX_STAGNANT_ROUNDS})."
            )
            if no_improve_rounds >= MAX_STAGNANT_ROUNDS:
                print("[loop] Stagnation threshold reached; stopping early.")
                break
        else:
            no_improve_rounds = 0

        # Prepare next round via Ollama refinement
        if r < max_rounds:
            if round_best_image is not None and round_best_score > 0:
                # Get fresh scores for the best round image to drive refinement
                _, clip_s, aesth_s = score_image(round_best_image, current_positive)
                current_positive, current_negative = refine_prompts_via_ollama(
                    current_positive,
                    current_negative,
                    best_score=round_best_score,
                    clip_score=clip_s,
                    aesth_score=aesth_s,
                    round_index=r,
                )
            else:
                print("[loop] No good candidate to refine from; keeping current prompts.")

    # Write manifest for asset browser
    try:
        if manifest_entries:
            manifest_path = assets_dir / "image_manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with manifest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest_entries, f, indent=2)
            print(f"[loop] Wrote image manifest to {manifest_path}")
    except Exception as e:
        print(f"[loop] Failed to write image manifest: {e}")

    # Finalize: copy best image into engine assets dir + summary + grid
    if best_global_image and best_global_image.exists():
        preview = assets_dir / "preview.png"
        best_out = assets_dir / "best_prompt_result.png"
        print(
            f"\n[loop] Best overall image = {best_global_image} "
            f"(score={best_global_score})"
        )
        print(f"[loop] Copying to {preview} and {best_out}")
        try:
            shutil.copy(best_global_image, preview)
            shutil.copy(best_global_image, best_out)
        except Exception as e:
            print(f"[loop] Failed to copy best image into assets: {e}")

        # Summary JSON for the content engine
        summary = {
            "project": project,
            "part": part,
            "best_score": best_global_score,
            "best_prompt": best_global_prompt,
            "best_image": str(best_global_image),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "target_score": target_score,
            "max_rounds": max_rounds,
            "variants_per_round": variants_per_round,
        }
        try:
            summary_json.parent.mkdir(parents=True, exist_ok=True)
            summary_json.write_text(json.dumps(summary, indent=2))
            print(f"[loop] Wrote summary JSON to {summary_json}")
        except Exception as e:
            print(f"[loop] Failed to write summary JSON: {e}")

        # Build a 3xN grid of top images (up to 9 best by score)
        try:
            top_entries = sorted(
                manifest_entries, key=lambda e: e["score"], reverse=True
            )[:9]
            grid_paths = [Path(e["filename"]) for e in top_entries]
            if grid_paths:
                grid_path = assets_dir / "grid.png"
                make_grid(grid_paths, grid_path, cols=3)
        except Exception as e:
            print(f"[loop] Failed to create grid from manifest: {e}")

        # Inject into blog draft for downstream pipeline
        try:
            inject_best_into_blog_draft(project, part, summary, BASE)
        except Exception as e:
            print(f"[loop] Blog injection error: {e}")
    else:
        print("[loop] No valid best image found; nothing to copy.")

    # 🔧 Clear queue again so Comfy isn't left chewing on anything else
    clear_comfy_queue(context="after optimizer job")

    print("\n[loop] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())