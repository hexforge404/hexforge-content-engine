#!/usr/bin/env python3
import asyncio
import json
import shutil
import subprocess
from pathlib import Path

from watchfiles import awatch, Change

# Base paths
BASE = Path("/mnt/hdd-storage/hexforge-content-engine")
INCOMING = BASE / "incoming-images"
ASSETS = BASE / "assets"
LOGS_PROCESSED = BASE / "logs" / "comfy-jobs" / "processed"
LOGS_FAILED = BASE / "logs" / "comfy-jobs" / "failed"

# 🔧 Paths to the two runners
SIMPLE_RUNNER = BASE / "linux" / "HexForgeEngine" / "scripts" / "simple_comfy_runner.py"
OPTIMIZER_RUNNER = BASE / "linux" / "HexForgeEngine" / "scripts" / "prompt-optimizer_old" / "loop_prompt_generator.py"

print(f"[watcher] Using SIMPLE_RUNNER = {SIMPLE_RUNNER}")
print(f"[watcher] Using OPTIMIZER_RUNNER = {OPTIMIZER_RUNNER}")
print(f"[watcher] Script file = {__file__}")


def ensure_dirs() -> None:
    """Make sure all expected directories exist."""
    INCOMING.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    LOGS_PROCESSED.mkdir(parents=True, exist_ok=True)
    LOGS_FAILED.mkdir(parents=True, exist_ok=True)


def move_to_processed(job_path: Path) -> None:
    LOGS_PROCESSED.mkdir(parents=True, exist_ok=True)
    dest = LOGS_PROCESSED / job_path.name
    job_path.replace(dest)


def move_to_failed(job_path: Path) -> None:
    LOGS_FAILED.mkdir(parents=True, exist_ok=True)
    dest = LOGS_FAILED / job_path.name
    job_path.replace(dest)


def run_comfy_job(runner_path: Path, project: str, part: str, prompt: str, num_images: int) -> bool:
    """Call the selected runner (simple or optimizer) as a subprocess."""

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

    # Build log text with job meta up top
    log_text = f"[JOB META] project={project} part={part} prompt={prompt!r} num_images={num_images}\n\n"
    log_text += proc.stdout or ""
    print(log_text)

    # Per-job log alongside images
    asset_dir = ASSETS / project / part / "images"
    asset_dir.mkdir(parents=True, exist_ok=True)
    with open(asset_dir / "comfy-last-run.log", "a", encoding="utf-8") as f:
        f.write("\n\n=== NEW RUN ===\n")
        f.write(log_text)

    return proc.returncode == 0


async def handle_job(job_path: Path) -> None:
    """Load a job JSON and route to the appropriate runner."""
    if not job_path.is_file() or job_path.suffix != ".json":
        return

    print(f"[watcher] Detected job: {job_path}")

    with job_path.open("r", encoding="utf-8") as f:
        job = json.load(f)

    project = job["project"]
    part = job["part"]
    prompt = job["prompt"]
    num_images = int(job.get("num_images", 1))
    engine = job.get("engine", "simple")  # "simple" or "optimizer"

    if engine == "optimizer":
        runner = OPTIMIZER_RUNNER
    else:
        runner = SIMPLE_RUNNER

    print(
        f"[JOB META] project={project} part={part} "
        f"engine={engine} prompt={prompt!r} num_images={num_images}"
    )

    ok = run_comfy_job(runner, project, part, prompt, num_images)

    if ok:
        print(f"[watcher] Job {job_path.name} -> OK")
        move_to_processed(job_path)
    else:
        print(f"[watcher] Job {job_path.name} -> FAILED")
        move_to_failed(job_path)


async def watch_loop() -> None:
    """Main watcher loop."""
    ensure_dirs()
    print(f"[watcher] Watching {INCOMING} (recursive=True)")

    # Process any jobs that already exist on startup
    for job in INCOMING.rglob("job-*.json"):
        await handle_job(job)

    # Live watch for new / updated jobs
    async for changes in awatch(INCOMING, recursive=True):
        for change, path_str in changes:
            if change in (Change.added, Change.modified) and path_str.endswith(".json"):
                await handle_job(Path(path_str))


if __name__ == "__main__":
    asyncio.run(watch_loop())
