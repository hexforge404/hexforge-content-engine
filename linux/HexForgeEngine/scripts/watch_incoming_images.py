#!/usr/bin/env python3
import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from watchfiles import awatch, Change

# ================================================================
# Paths
# ================================================================
BASE = Path("/mnt/hdd-storage/hexforge-content-engine")
INCOMING = BASE / "incoming-images"
ASSETS = BASE / "assets"
LOGS_PROCESSED = BASE / "logs" / "comfy-jobs" / "processed"
LOGS_FAILED = BASE / "logs" / "comfy-jobs" / "failed"

SIMPLE_RUNNER = BASE / "linux/HexForgeEngine/scripts/simple_comfy_runner.py"
OPTIMIZER_RUNNER = BASE / "linux/HexForgeEngine/scripts/loop_prompt_generator.py"

print(f"[watcher] Using SIMPLE_RUNNER = {SIMPLE_RUNNER}")
print(f"[watcher] Using OPTIMIZER_RUNNER = {OPTIMIZER_RUNNER}")
print(f"[watcher] Script file = {__file__}")


# ================================================================
# Directory setup
# ================================================================
def ensure_dirs():
    INCOMING.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    LOGS_PROCESSED.mkdir(parents=True, exist_ok=True)
    LOGS_FAILED.mkdir(parents=True, exist_ok=True)


# ================================================================
# Move job to processed/failed
# ================================================================
def move_to_processed(job_path: Path):
    LOGS_PROCESSED.mkdir(parents=True, exist_ok=True)
    shutil.move(str(job_path), LOGS_PROCESSED / job_path.name)

def move_to_failed(job_path: Path):
    LOGS_FAILED.mkdir(parents=True, exist_ok=True)
    shutil.move(str(job_path), LOGS_FAILED / job_path.name)


# ================================================================
# Run a job with either runner
# ================================================================
def run_comfy_job(runner_path: Path, project: str, part: str, prompt: str, num_images: int) -> bool:
    cmd = [
        "python3",
        str(runner_path),
        "--project", project,
        "--part", part,
        "--prompt", prompt,
        "--num-images", str(num_images),
    ]

    print(f"[comfy] Running: {' '.join(cmd)}")

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    log_text = f"[JOB META] project={project} part={part} prompt={prompt!r} num_images={num_images}\n\n"
    log_text += proc.stdout or ""

    print(log_text)

    # Write a last-run log into the asset directory
    asset_dir = ASSETS / project / part / "images"
    asset_dir.mkdir(parents=True, exist_ok=True)
    with open(asset_dir / "comfy-last-run.log", "a", encoding="utf-8") as f:
        f.write("\n\n=== NEW RUN ===\n")
        f.write(log_text)

    return proc.returncode == 0


# ================================================================
# Handle job file (SYNC — no await)
# ================================================================
def handle_job(job_path: Path):
    print(f"[watcher] Detected job: {job_path}")

    with job_path.open("r") as f:
        job = json.load(f)

    project = job["project"]
    part = job["part"]
    prompt = job["prompt"]
    num_images = int(job.get("num_images", 1))
    engine = job.get("engine", "simple")

    # Choose runner
    runner = OPTIMIZER_RUNNER if engine == "optimizer" else SIMPLE_RUNNER

    print(f"[JOB META] project={project} part={part} engine={engine} prompt={prompt!r} num_images={num_images}")

    ok = run_comfy_job(runner, project, part, prompt, num_images)

    if ok:
        print(f"[watcher] Job {job_path.name} -> OK")
        move_to_processed(job_path)
    else:
        print(f"[watcher] Job {job_path.name} -> FAILED")
        move_to_failed(job_path)


# ================================================================
# Async file-watching loop (does NOT await handle_job)
# ================================================================
async def watch_loop():
    ensure_dirs()
    print(f"[watcher] Watching {INCOMING} (recursive=True)")

    # Process existing jobs first
    for job in INCOMING.rglob("job-*.json"):
        handle_job(job)

    # Watch for new jobs
    async for changes in awatch(INCOMING, recursive=True):
        for change, path_str in changes:
            if path_str.endswith(".json") and change in (Change.added, Change.modified):
                handle_job(Path(path_str))


# ================================================================
# Entry point
# ================================================================
if __name__ == "__main__":
    asyncio.run(watch_loop())
# ================================================================
