#!/usr/bin/env python3
import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path

from watchfiles import awatch, Change

BASE = Path("/mnt/hdd-storage/hexforge-content-engine")
INCOMING = BASE / "incoming-images"
ASSETS = BASE / "assets"
LOGS_PROCESSED = BASE / "logs" / "comfy-jobs" / "processed"
LOGS_FAILED = BASE / "logs" / "comfy-jobs" / "failed"

# 🔧 Path to your existing ComfyUI runner
# Adjust if your script lives somewhere else
COMFY_RUNNER = BASE / "loop_prompt_generator.py"


def ensure_dirs():
    INCOMING.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    LOGS_PROCESSED.mkdir(parents=True, exist_ok=True)
    LOGS_FAILED.mkdir(parents=True, exist_ok=True)


def run_comfy_job(project: str, part: str, prompt: str, num_images: int) -> bool:
    """
    Call your Comfy pipeline.
    This assumes loop_prompt_generator.py accepts these CLI args:
      --prompt, --project, --part, --num-images
    Tweak the args if your script differs.
    """
    cmd = [
        "python",
        str(COMFY_RUNNER),
        "--prompt",
        prompt,
        "--project",
        project,
        "--part",
        part,
        "--num-images",
        str(num_images),
    ]
    print(f"[comfy] Running: {' '.join(cmd)}")

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    log_text = proc.stdout or ""
    print(log_text)

    # Optional: write a per-job log
    asset_dir = ASSETS / project / part / "images"
    asset_dir.mkdir(parents=True, exist_ok=True)
    with open(asset_dir / "comfy-last-run.log", "a", encoding="utf-8") as f:
        f.write("\n\n=== NEW RUN ===\n")
        f.write(log_text)

    return proc.returncode == 0


async def handle_job(job_path: Path):
    if not job_path.is_file() or not job_path.suffix == ".json":
        return

    print(f"[watcher] Detected job: {job_path}")

    # Load job data
    with open(job_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    project = data.get("project", "default")
    part = data.get("part", "part1")
    prompt = data.get("prompt", "")
    num_images = int(data.get("num_images", 4))

    # Run Comfy
    ok = run_comfy_job(project, part, prompt, num_images)

    # Move job file to processed / failed logs
    target_dir = LOGS_PROCESSED if ok else LOGS_FAILED
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(job_path), target_dir / job_path.name)

    status = "OK" if ok else "FAILED"
    print(f"[watcher] Job {job_path.name} -> {status}")


async def watch_loop():
    ensure_dirs()
    print(f"[watcher] Watching {INCOMING} (recursive=True)")

    # Process any jobs that already exist on startup
    for job in INCOMING.rglob("job-*.json"):
        await handle_job(job)

    async for changes in awatch(INCOMING, recursive=True):
        for change, path_str in changes:
            if change in (Change.added, Change.modified) and path_str.endswith(".json"):
                await handle_job(Path(path_str))


if __name__ == "__main__":
    asyncio.run(watch_loop())
# To run this script, ensure you have watchfiles installed:
# pip install watchfiles
# Then execute:
# python scripts/watch_incoming_images.py