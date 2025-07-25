# refine_prompt_loop.py

import json
import time
import subprocess
from loop_prompt_generator import build_prompt_json, post_to_comfyui

prompt = input("Enter base prompt: ")
neg_prompt = input("Enter negative prompt: ")
attempts = int(input("How many variants to test? "))

for i in range(attempts):
    variant = f"{prompt} [variant {i+1}]"
    payload = build_prompt_json(variant, neg_prompt, f"test_variant_{i}")
    print(f"[INFO] Submitting variant {i+1}...")
    success = post_to_comfyui(payload)
    if not success:
        print(f"[ERROR] Failed to submit variant {i+1}")
    else:
        print("[INFO] Waiting 20s for generation...")
        time.sleep(20)
    print(f"[INFO] Scoring variant {i+1}...")
    try:
        result = subprocess.run([
            "python3", "score_image.py",
            "--image", f"output/test_variant_{i}_00001_.png",
            "--prompt", variant,
            "--mode", "both"
        ], capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        print(f"[INFO] Variant {i+1} scores: {output}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Scoring failed for variant {i+1}: {e}")
    time.sleep(5)  # Give some time before next iteration   
    print(f"[INFO] Finished processing variant {i+1}\n")    
# End of refine_prompt_loop.py