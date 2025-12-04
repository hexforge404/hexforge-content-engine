from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import subprocess
import uuid
import os

app = FastAPI(title="HexForge Media API")

CONTENT_ROOT = Path("/mnt/hdd-storage/hexforge-content-engine")
SADTALKER_ROOT = Path("/root/ai-tools/SadTalker")
WHISPER_ROOT = Path("/root/ai-tools/Whisper")
COMFY_ROOT = Path("/root/ai-tools/ComfyUI")


class TTSRequest(BaseModel):
    text: str
    project: str | None = None
    part: str | None = None
    voice: str | None = None  # if your tts_from_text has a voice arg


class STTRequest(BaseModel):
    audio_path: str  # absolute path on server, or you can later add upload
    project: str | None = None
    part: str | None = None


class ImageRequest(BaseModel):
    project: str
    part: str
    min_score: float | None = 7.5


@app.get("/health")
def health():
    return {"status": "ok"}


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
        # activate venv + run your wrapper
        f"cd {SADTALKER_ROOT} && "
        f"source venv/bin/activate && "
        f"python scripts/tts_from_text.py "
        f"--text {sh_quote(req.text)} "
        f"--out {sh_quote(str(out_path))}"
    ]
    if req.voice:
        cmd[-1] += f" --voice {sh_quote(req.voice)}"

    try:
        subprocess.check_call(" ".join(cmd), shell=True)
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"TTS failed: {e}"}

    return {"ok": True, "path": str(out_path)}


@app.post("/stt")
def stt(req: STTRequest):
    """
    Very first pass: assumes transcribe-audio.sh takes an audio/video path
    and prints transcript to stdout. If yours writes to file instead,
    tweak this accordingly.
    """
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
        f"cd {WHISPER_ROOT} && "
        f"source venv/bin/activate && "
        f"./transcribe-audio.sh {sh_quote(str(audio_path))} > {sh_quote(str(out_file))}"
    ]

    try:
        subprocess.check_call(" ".join(cmd), shell=True)
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"STT failed: {e}"}

    try:
        text = out_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "error": f"Failed to read transcript: {e}"}

    return {"ok": True, "path": str(out_file), "transcript": text}


@app.post("/image-loop")
def image_loop(req: ImageRequest):
    """
    Kick off your ComfyUI prompt loop via run-generator.sh.
    This just returns the assets path for now.
    """
    project = req.project
    part = req.part
    min_score = req.min_score or 7.5

    assets_dir = CONTENT_ROOT / "assets" / project / part
    assets_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "bash",
        "-lc",
        f"cd {COMFY_ROOT} && "
        f"source venv/bin/activate && "
        f"./run-generator.sh "
        f"--min_score {min_score} "
        f"--final_variant_mode best_prompt"
    ]

    try:
        subprocess.check_call(" ".join(cmd), shell=True)
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"Image loop failed: {e}"}

    # For now we just return the assets directory;
    # we can later inspect logs / image_scores_run.json to pick preview.png
    return {"ok": True, "assets_dir": str(assets_dir)}
