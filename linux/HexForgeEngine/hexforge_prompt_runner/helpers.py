import subprocess
import os
import json
import time
import csv
from datetime import datetime
import graphviz
import requests
import re
import os
import time

def wait_for_file(filepath, timeout=10):
    start_time = time.time()
    while not os.path.exists(filepath):
        if time.time() - start_time > timeout:
            raise FileNotFoundError(f"[ERROR] File not found after timeout: {filepath}")
        print(f"[WAIT] Waiting for image to appear: {filepath}")
        time.sleep(0.5)

# === Prompt Cleaner ===
def clean_prompt_for_shell(text, max_words=50, max_chars=200):
    txt = re.sub(r"\(.*?\)", "", text)  # remove (optional) detail
    txt = txt.replace('"', '').replace('`', '').replace('$', '')
    txt = txt.replace('--', '—')
    txt = ' '.join(txt.split())
    txt = txt.rstrip('.,')
    words = txt.split()
    if len(words) > max_words:
        txt = ' '.join(words[:max_words])
        print(f"[WARN] Truncated to {max_words} words")
    if len(txt) > max_chars:
        txt = txt[:max_chars]
        print(f"[WARN] Truncated to {max_chars} chars")
    return txt

# === Score Image Using External Script ===
def rate_generated_image(filename, prompt, config=None):
    try:
        abs_path = os.path.abspath(filename)
        wait_for_file(abs_path)
        clean = clean_prompt_for_shell(prompt)

        # Use configured script path or fallback
        score_script = (
            config.get("score_script")
            if config and config.get("score_script")
            else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "score_image.py"))
        )


        if not os.path.isfile(score_script):
            print(f"[ERROR] Scoring script not found: {score_script}")
            return 0, 0, 0

        result = subprocess.run([
            os.path.abspath(score_script),
            "--image", abs_path,
            "--prompt", clean,
            "--mode", "both"
        ], capture_output=True, text=True)

        print(f"[DEBUG] Running scoring script: {score_script}")
        print(f"[DEBUG] Scoring script stdout:\n{result.stdout}")
        print(f"[DEBUG] Scoring script stderr:\n{result.stderr}")

        result.check_returncode()
        if result.returncode != 0:
            print(f"[ERROR] Scoring script failed with code {result.returncode}")
            return 0, 0, 0



        data = json.loads(result.stdout)
        clip = data.get("clip_score", 0)
        aesthetic = data.get("aesthetic_score", 0)
        total = round((clip * 10 + aesthetic) / 2, 2)
        return total, clip, aesthetic

    except Exception as e:
        print(f"[ERROR] Scoring failed: {e}")
        return 0, 0, 0


# === Save Results to CSV ===
def log_result(filename, prompt, neg_prompt, total_score, clip, aesthetic, log_path=None, config=None):
    if config and not log_path:
        log_path = config.get("log_file")
    if not log_path:
        print("[WARN] No log path provided.")
        return

    exists = os.path.isfile(log_path)
    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["filename", "prompt", "negative_prompt", "score", "clip", "aesthetic", "timestamp"])
        writer.writerow([filename, prompt, neg_prompt, total_score, clip, aesthetic, datetime.now().isoformat()])

# === Visualize Attempts ===
def draw_prompt_score_graph(attempts, output_path):
    dot = graphviz.Digraph(comment='Prompt Variants', format='png')
    for idx, att in enumerate(attempts):
        label = f"#{idx+1}: {att['score']}\n{att['prompt'][:40]}..."
        dot.node(str(idx), label=label)
        if idx > 0:
            dot.edge(str(idx - 1), str(idx))
    dot.render(output_path, cleanup=True)

# === Retryable ComfyUI POST ===
def post_to_comfyui(prompt_json, comfy_url=None, config=None, retries=3):
    comfy_url = comfy_url or (config.get("comfyui_url") if config else "http://localhost:8188/prompt")
    for attempt in range(1, retries + 1):
        try:
            print(f"[DEBUG] Posting to ComfyUI (Attempt {attempt})")
            response = requests.post(
                comfy_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(prompt_json)
            )
            if response.ok:
                return True
        except Exception as e:
            print(f"[WARN] Attempt {attempt} failed: {e}")
        time.sleep(2)
    print("[ERROR] All retries failed.")
    return False
