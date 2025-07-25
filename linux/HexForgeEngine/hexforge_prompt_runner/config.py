import os
import json

config = {
    "prompt_base": "AI control room with glowing monitors and command chairs, transparent interface panels, exposed wires and cooling ducts, cyberpunk style with cinematic lighting and ambient neon reflections, wide lens perspective.",
    "negative_prompt": "low resolution, deformed, blurry, missing screens, dull lighting",
    "comfyui_url": "http://localhost:8188/prompt",
    "llm_model": "mistral",
    "output_dir": "/mnt/hdd-storage/hexforge-content-engine/assets/ai_control_room/part1/images",
    "log_file": "/mnt/hdd-storage/hexforge-content-engine/assets/ai_control_room/part1/logs/image_scores.csv",
    "filename_prefix": "ai_control_room_loop",
    "prompt_template_file": "templates/prompt_templates.json",
    "prompt_guidelines_file": "templates/prompt_guidelines.txt",
    "prompt_template_name": "",
    "prompt_guidelines": "",
    "prompt_templates": {},

    "max_seeds_total": 3,
    "max_seed_refinements": 2,
    "max_stale": 2,
    "retry": 3,
    "sleep_after_prompt": 30,
    "final_variants": 2,

    "use_llava": True,
    "no_guideline_repeat": False
}

def load_config(args):
    new_config = config.copy()
    new_config.update({
        "project_name": args.project_name,
        "output_dir": args.output_dir or config["output_dir"],
        "max_seeds_total": args.max_seeds_total,
        "max_seed_refinements": args.max_seed_refinements,
        "min_score": args.min_score,
        "retry": args.retry,
        "sleep_after_prompt": args.sleep,
        "use_llava": args.use_llava,
        "final_variant_mode": args.final_variant_mode,
    })
    validate_config_files(new_config)
    return new_config

def validate_config_files(cfg):
    missing = []
    if cfg.get("prompt_template_file") and not os.path.isfile(cfg["prompt_template_file"]):
        missing.append(cfg["prompt_template_file"])
    if cfg.get("prompt_guidelines_file") and not os.path.isfile(cfg["prompt_guidelines_file"]):
        missing.append(cfg["prompt_guidelines_file"])
    if missing:
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

def save_config_to_file(cfg, path):
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)

def get_output_dir(config):
    if config.get("output_dir"):
        return config["output_dir"]
    return os.path.join("/mnt/hdd-storage/hexforge-content-engine/assets", config["project_name"], "images")

def get_log_file(config):
    if config.get("log_file"):
        return config["log_file"]
    return os.path.join("/mnt/hdd-storage/hexforge-content-engine/assets", config["project_name"], "logs", "image_scores.csv")

def get_filename_prefix(config):
    if config.get("filename_prefix"):
        return config["filename_prefix"]
    return f"{config['project_name']}_loop" if config.get("project_name") else "loop"

def get_prompt_template_name(config):
    return config.get("prompt_template_name", "")

def get_prompt_templates(config):
    if config.get("prompt_templates"):
        return config["prompt_templates"]
    template_file = config.get("prompt_template_file", "templates/prompt_templates.json")
    if os.path.exists(template_file):
        with open(template_file, "r") as f:
            return json.load(f)
    return {}

def get_prompt_guidelines(config):
    if config.get("prompt_guidelines"):
        return config["prompt_guidelines"]
    guidelines_file = config.get("prompt_guidelines_file", "templates/prompt_guidelines.txt")
    if os.path.exists(guidelines_file):
        with open(guidelines_file, "r") as f:
            return f.read().strip()
    return ""

def get_no_guideline_repeat(config):
    return config.get("no_guideline_repeat", False)

def get_use_llava(config):
    return config.get("use_llava", True)

def get_llm_model(config):
    return config.get("llm_model", "mistral")

def get_max_seeds_total(config):
    return config.get("max_seeds_total", 3)

def get_max_seed_refinements(config):
    return config.get("max_seed_refinements", 2)

def get_max_stale(config):
    return config.get("max_stale", 2)

def get_retry_count(config):
    return config.get("retry", 3)

def get_sleep_after_prompt(config):
    return config.get("sleep_after_prompt", 30)

def get_final_variants(config):
    return config.get("final_variants", 2)

def get_final_variant_mode(config):
    return config.get("final_variant_mode", "best_prompt")
