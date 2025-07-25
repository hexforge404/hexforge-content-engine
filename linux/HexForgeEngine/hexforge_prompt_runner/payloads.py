import random

def build_prompt_json(prompt_text, neg_text, prefix, config):
    return {
        "prompt": {
            "0": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd15.ckpt"}},
            "1": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["0", 1], "text": prompt_text}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["0", 1], "text": neg_text}},
            "3": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1}},
            "4": {"class_type": "KSampler", "inputs": {
                "model": ["0", 0], "positive": ["1", 0], "negative": ["2", 0],
                "latent_image": ["3", 0],
                "steps": 25, "cfg": 7.5, "sampler_name": "euler", "scheduler": "normal", "denoise": 1,
                "seed": random.randint(0, 999999)
            }},
            "5": {"class_type": "VAEDecode", "inputs": {"samples": ["4", 0], "vae": ["0", 2]}},
            "6": {"class_type": "SaveImage", "inputs": {
                "images": ["5", 0],
                "filename_prefix": prefix,
                "output_path": config["output_dir"]
            }}
        }
    }
