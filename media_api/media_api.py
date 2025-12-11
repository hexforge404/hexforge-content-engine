import shlex
from pathlib import Path
from datetime import datetime
import subprocess
import json
import os

from fastapi import FastAPI
from pydantic import BaseModel

from .media_jobs import queue_image_job, queue_voice_job
import uuid



app = FastAPI(title="HexForge Media API")

CONTENT_ROOT = Path("/mnt/hdd-storage/hexforge-content-engine")
SADTALKER_ROOT = Path("/root/ai-tools/SadTalker")
WHISPER_ROOT = Path("/root/ai-tools/Whisper")
COMFY_ROOT = Path("/root/ai-tools/ComfyUI")


def sh_quote(s: str) -> str:
    return shlex.quote(str(s))


class TTSRequest(BaseModel):
    text: str
    project: str | None = None
    part: str | None = None
    voice: str | None = None


class STTRequest(BaseModel):
    audio_path: str
    project: str | None = None
    part: str | None = None


class ImageRequest(BaseModel):
    project: str
    part: str
    min_score: float | None = 7.5


class BlogJsonRequest(BaseModel):
    text: str
    project: str
    part: str | None = None


class QueueImageJobRequest(BaseModel):
    project: str
    part: str
    prompt: str
    num_images: int = 4


class QueueVoiceJobRequest(BaseModel):
    project: str
    part: str
    text: str
    voice: str | None = "default"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/blog-json")
async def blog_json(req: BlogJsonRequest):
    """
    Accept a simple blog JSON payload from the assistant and
    save it into the content-engine tree so the pipeline can
    pick it up later.
    """
    base_dir = CONTENT_ROOT / "incoming-blogs" / req.project
    base_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    part = req.part or "part"
    out_path = base_dir / f"{part}-{ts}.json"

    payload = req.model_dump()
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {
        "status": "ok",
        "saved": str(out_path),
        "project": req.project,
        "part": part,
    }


# -----------------------
#  Media job queue APIs
# -----------------------

@app.post("/media/queue/image")
def media_queue_image(req: QueueImageJobRequest):
    """
    Queue an image-generation job for the ComfyUI watcher.

    Writes a job-*.json file under:
      /mnt/hdd-storage/hexforge-content-engine/incoming-images/<project>/<part>/
    """
    job_path = queue_image_job(
        project=req.project,
        part=req.part,
        prompt=req.prompt,
        num_images=req.num_images,
    )
    return {
        "ok": True,
        "job_path": job_path,
        "project": req.project,
        "part": req.part,
    }


@app.post("/media/queue/voice")
def media_queue_voice(req: QueueVoiceJobRequest):
    """
    Queue a voice-generation job (TTS) for the watcher pipeline.

    Writes a job-*.json file under:
      /mnt/hdd-storage/hexforge-content-engine/incoming-voice/<project>/<part>/
    """
    job_path = queue_voice_job(
        project=req.project,
        part=req.part,
        text=req.text,
        voice=req.voice or "default",
    )
    return {
        "ok": True,
        "job_path": job_path,
        "project": req.project,
        "part": req.part,
    }


# -----------------------
#  Direct TTS / STT APIs
# -----------------------

@app.post("/tts")
def tts(req: TTSRequest):
    project = req.project or "scratch"
    part = req.part or "part-1"

    out_dir = CONTENT_ROOT / "assets" / project / part / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"tts-{uuid.uuid4().hex}.wav"

    cmd = [
        "bash",
        "-lc",
        (
            f"cd {SADTALKER_ROOT} && "
            f"source venv/bin/activate && "
            f"python scripts/tts_from_text.py "
            f"--text {sh_quote(req.text)} "
            f"--out {sh_quote(str(out_path))}"
        ),
    ]
    if req.voice:
        cmd[-1] += f" --voice {sh_quote(req.voice)}"

    try:
        subprocess.check_call(" ".join(cmd), shell=True, executable="/bin/bash")
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"TTS failed: {e}"}

    return {"ok": True, "path": str(out_path)}


@app.post("/stt")
def stt(req: STTRequest):
    audio_path = Path(req.audio_path)
    if not audio_path.exists():
        return {"ok": False, "error": f"File not found: {audio_path}"}

    project = req.project or "scratch"
    part = req.part or "part-1"
    out_dir = CONTENT_ROOT / "assets" / project / part / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"transcript-{uuid.uuid4().hex}.txt"

    cmd = [
        "bash",
        "-lc",
        (
            f"cd {WHISPER_ROOT} && "
            f"source venv/bin/activate && "
            f"./transcribe-audio.sh {sh_quote(str(audio_path))} "
            f"> {sh_quote(str(out_file))}"
        ),
    ]

    try:
        subprocess.check_call(" ".join(cmd), shell=True, executable="/bin/bash")
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"STT failed: {e}"}

    try:
        text = out_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "error": f"Failed to read transcript: {e}"}

    return {"ok": True, "path": str(out_file), "transcript": text}


# -----------------------
#  Legacy image-loop API
# -----------------------

@app.post("/image-loop")
def image_loop(req: ImageRequest):
    project = req.project
    part = req.part
    min_score = req.min_score or 7.5

    assets_dir = CONTENT_ROOT / "assets" / project / part
    assets_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "bash",
        "-lc",
        (
            f"cd {COMFY_ROOT} && "
            f"source venv/bin/activate && "
            f"./run-generator.sh "
            f"--min_score {min_score} "
            f"--final_variant_mode best_prompt"
        ),
    ]

    try:
        subprocess.check_call(" ".join(cmd), shell=True, executable="/bin/bash")
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"Image loop failed: {e}"}

    return {"ok": True, "assets_dir": str(assets_dir)}
