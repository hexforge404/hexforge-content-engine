# score_image.py

import argparse
import torch
from PIL import Image
import torchvision.transforms as transforms
import clip
import json

def load_image(image_path):
    image = Image.open(image_path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])
    return transform(image).unsqueeze(0)

def load_clip_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess, device

def score_clip(image_tensor, prompt, model, preprocess, device):
    image = preprocess(Image.fromarray((image_tensor.squeeze().permute(1,2,0).numpy()*255).astype('uint8'))).unsqueeze(0).to(device)
    text = clip.tokenize([prompt]).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = (image_features @ text_features.T).item()
    return round(similarity, 4)

def score_aesthetic(image_tensor):
    # Stub: Replace with your aesthetic model or hardcoded example
    return 5.0 + (torch.rand(1).item() * 5.0)  # Simulated 5–10 range

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--mode", choices=["clip", "aesthetic", "both"], default="both")
    args = parser.parse_args()

    image_tensor = load_image(args.image)
    model, preprocess, device = load_clip_model()

    result = {}
    if args.mode in ["clip", "both"]:
        result["clip_score"] = score_clip(image_tensor, args.prompt, model, preprocess, device)
    if args.mode in ["aesthetic", "both"]:
        result["aesthetic_score"] = score_aesthetic(image_tensor)

    print(json.dumps(result))

if __name__ == "__main__":
    main()
