#!/usr/bin/env python3
import argparse
import json
import random

# Try to import heavy deps (torch + CLIP). If they aren't available,
# we fall back to a lightweight heuristic scorer.
TORCH_AVAILABLE = False
IMPORT_ERROR = None

try:
    import torch
    from PIL import Image
    import torchvision.transforms as transforms
    import clip  # type: ignore

    TORCH_AVAILABLE = True
except Exception as e:
    IMPORT_ERROR = e
    # We only need PIL for the fallback path
    try:
        from PIL import Image  # type: ignore
    except Exception:
        Image = None  # type: ignore


def load_image(image_path):
    """
    Load an image as a torch tensor for CLIP.
    Only used when TORCH_AVAILABLE is True.
    """
    image = Image.open(image_path).convert("RGB")
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ]
    )
    return transform(image).unsqueeze(0)


def load_clip_model():
    """
    Load CLIP model and preprocess. Only called when TORCH_AVAILABLE is True.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess, device


def score_clip(image_tensor, prompt, model, preprocess, device) -> float:
    """
    Real CLIP score: cosine similarity between image and text.
    """
    img_np = (image_tensor.squeeze().permute(1, 2, 0).numpy() * 255).astype("uint8")
    image = preprocess(Image.fromarray(img_np)).unsqueeze(0).to(device)
    text = clip.tokenize([prompt]).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = (image_features @ text_features.T).item()
    return round(float(similarity), 4)


def heuristic_aesthetic_score(image_path: str) -> float:
    """
    Lightweight "aesthetic" score that does NOT require torch.
    Uses basic image statistics + randomness just to give non-zero variety.
    Range roughly 5–10, like your stub.
    """
    if Image is None:
        # Absolute worst case: PIL missing too
        return round(random.uniform(5.0, 10.0), 3)

    img = Image.open(image_path).convert("L")  # grayscale
    # Simple stats: brightness and contrast
    hist = img.histogram()
    total = sum(hist)
    if total == 0:
        return round(random.uniform(5.0, 10.0), 3)

    # Normalized histogram
    probs = [h / total for h in hist]
    # Brightness estimate
    brightness = sum(i * p for i, p in enumerate(probs)) / 255.0  # 0–1
    # Contrast estimate
    variance = sum(((i / 255.0 - brightness) ** 2) * p for i, p in enumerate(probs))
    contrast = variance ** 0.5  # stddev 0–~0.5

    # Map brightness + contrast to a 0–1-ish score
    base = 0.4 * brightness + 0.6 * contrast
    # Add a tiny bit of randomness for tie-breaking
    jitter = random.uniform(-0.05, 0.05)
    raw = max(0.0, min(1.0, base + jitter))

    # Scale to 5–10
    return round(5.0 + raw * 5.0, 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--mode", choices=["clip", "aesthetic", "both"], default="both"
    )
    args = parser.parse_args()

    result = {}

    if TORCH_AVAILABLE:
        # Full CLIP + torch path
        try:
            image_tensor = load_image(args.image)
            model, preprocess, device = load_clip_model()

            if args.mode in ["clip", "both"]:
                result["clip_score"] = score_clip(
                    image_tensor, args.prompt, model, preprocess, device
                )
            if args.mode in ["aesthetic", "both"]:
                # You can replace this later with a real aesthetic model
                result["aesthetic_score"] = heuristic_aesthetic_score(args.image)

        except Exception as e:
            # If anything goes wrong in the heavy path, fall back to heuristic
            result["clip_score"] = 0.0
            result["aesthetic_score"] = heuristic_aesthetic_score(args.image)
            result["error"] = f"heavy_scoring_failed: {type(e).__name__}: {e}"

    else:
        # Fallback path: no torch/CLIP installed, use heuristic only
        result["clip_score"] = 0.0  # we simply don't have CLIP here
        result["aesthetic_score"] = heuristic_aesthetic_score(args.image)
        if IMPORT_ERROR is not None:
            result["warning"] = f"torch_or_clip_unavailable: {type(IMPORT_ERROR).__name__}"

    print(json.dumps(result))


if __name__ == "__main__":
    main()
