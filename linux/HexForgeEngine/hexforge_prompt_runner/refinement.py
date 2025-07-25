import requests
import base64
import os
import time

# === Template injection ===
def apply_prompt_template(template_name, description, TEMPLATES):
    if template_name in TEMPLATES:
        template = TEMPLATES[template_name]
        return template.replace("{{DESCRIPTION}}", description.strip())
    return description

# === Guidelines injection ===
def apply_guidelines(prompt, guidelines="", allow_repeat=True, no_repeat=False):
    if guidelines and allow_repeat and not no_repeat:
        return f"{guidelines.strip()}\n\n{prompt.strip()}"
    return prompt

# === Final formatting ===
def build_final_prompt(raw_prompt, config, allow_guidelines=True):
    template_name = config.get("prompt_template_name", "")
    templates = config.get("prompt_templates", {})
    guidelines = config.get("prompt_guidelines", "")
    no_repeat = config.get("no_guideline_repeat", False)

    templated = apply_prompt_template(template_name, raw_prompt, templates)
    return apply_guidelines(templated, guidelines, allow_repeat=allow_guidelines and not no_repeat)

# === Main refinement function ===
def refine_prompt_with_llm(prev_prompt, score, attempt_num, preview_path, config, run_log):
    print(f"[DEBUG] Refining prompt on attempt #{attempt_num} with score {score:.2f}")

    if config.get("min_score") and score < run_log.get("best_score", 0):
        print(f"[INFO] Current score {score:.2f} is lower than best. Reusing.")
        prev_prompt = run_log.get("best_prompt", prev_prompt)
        preview_path = run_log.get("best_image", preview_path)

    if preview_path and os.path.exists(preview_path) and config.get("use_llava"):
        try:
            print("[INFO] Using LLaVA for multimodal refinement")
            with open(preview_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            payload = {
                "model": config["llm_model"],
                "prompt": (
                    f"You are a prompt optimization assistant. Based on this image and the original Stable Diffusion prompt, "
                    f"generate a stronger visual prompt.\n\nOriginal Prompt: {prev_prompt}\n\nImproved Prompt:"
                ),
                "stream": False,
                "images": [encoded]
            }
            for i in range(3):
                try:
                    print(f"[DEBUG] Sending payload to LLaVA (attempt {i+1})")
                    r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
                    suggestion = r.json().get("response") or r.json().get("text")
                    if suggestion:
                        return build_final_prompt(suggestion.strip(), config, allow_guidelines=False)
                except Exception as e:
                    print(f"[LLaVA ERROR] (attempt {i+1}) {e}")
                    time.sleep(2)
            print("[WARN] All LLaVA attempts failed. Falling back.")
        except Exception as e:
            print(f"[LLaVA ERROR] {e}")

    try:
        prompt_text = (
            f"You are a prompt refinement model. Improve the following Stable Diffusion prompt for better composition and aesthetics.\n"
            f"Prompt: {prev_prompt}\nScore: {score:.2f}\n\nImproved Prompt:"
        )
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": config["llm_model"], "prompt": prompt_text, "stream": False},
            timeout=120
        )
        suggestion = r.json().get("response") or r.json().get("text")
        if suggestion:
            return build_final_prompt(suggestion.strip(), config, allow_guidelines=False)
    except Exception as e:
        print(f"[LLM ERROR] {e}")

    return build_final_prompt(prev_prompt, config, allow_guidelines=False)
