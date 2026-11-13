
import os
import json
import base64
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageOps
from io import BytesIO

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

MODEL = "@cf/black-forest-labs/flux-1-schnell"

OUTPUT_DIR = BASE_DIR / "output" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def main():

    if not ACCOUNT_ID or not API_TOKEN:
        raise ValueError("Cloudflare credentials missing from .env")

    story_file = BASE_DIR / "output" / "story.json"

    with open(story_file, "r", encoding="utf-8") as file:
        story = json.load(file)

    scenes = story.get("scenes", [])

    if not scenes:
        raise ValueError("No scenes found in story.json")

    scene = scenes[0]

    visual_prompt = scene.get("visual_prompt", "")

    if not visual_prompt:
        visual_prompt = scene.get("narration", "")

    if not visual_prompt:
        raise ValueError("First scene has no visual prompt or narration")

    prompt = (
        "Create a beautiful 2D cartoon illustration for a Hindi "
        "children's story. Follow this scene description exactly. "
        "Show the correct human or animal characters. "
        "Do not add unrelated characters. "
        "Bright colors, expressive faces, family-friendly storybook art. "
        + visual_prompt
    )

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        + ACCOUNT_ID
        + "/ai/run/"
        + MODEL
    )

    headers = {
        "Authorization": "Bearer " + API_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "steps": 4
    }

    print("Generating first story image using Cloudflare...")

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180
    )

    if not response.ok:
        print("Cloudflare error:", response.status_code)
        print(response.text[:2000])
        response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    if "image/" in content_type:
        image_bytes = response.content
    else:
        result = response.json()
        image_data = result.get("result", {}).get("image")

        if not image_data:
            raise RuntimeError(
                "Image data not found in Cloudflare response: "
                + str(result)[:1000]
            )

        image_bytes = base64.b64decode(image_data)

    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    image = ImageOps.fit(
        image,
        (1280, 720),
        method=Image.Resampling.LANCZOS
    )

    output_file = OUTPUT_DIR / "cloudflare_test.png"

    image.save(output_file)

    print("\nImage generated successfully!")
    print("Story:", story.get("title"))
    print("Scene prompt:", visual_prompt)
    print("Saved:", output_file)


if __name__ == "__main__":
    main()
