# /mnt/hdd-storage/hexforge-content-engine/media_api/media_jobs.py
from pathlib import Path
from datetime import datetime
import json

BASE = Path("/mnt/hdd-storage/hexforge-content-engine")

def queue_image_job(project: str, part: str, prompt: str, num_images: int = 4):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = BASE / "incoming-images" / project / part
    folder.mkdir(parents=True, exist_ok=True)
    job_path = folder / f"job-{ts}.json"
    payload = {
        "project": project,
        "part": part,
        "prompt": prompt,
        "num_images": num_images,
        "workflow": "hexforge-default",
    }
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return str(job_path)

def queue_voice_job(project: str, part: str, text: str, voice: str = "default"):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = BASE / "incoming-voice" / project / part
    folder.mkdir(parents=True, exist_ok=True)
    job_path = folder / f"job-{ts}.json"
    payload = {
        "project": project,
        "part": part,
        "text": text,
        "voice": voice,
    }
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return str(job_path)
