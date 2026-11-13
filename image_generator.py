
import os
import time
import base64
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image, ImageOps
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "output" / "images"

WIDTH = 1280
HEIGHT = 720

MODEL = "@cf/black-forest-labs/flux-1-schnell"

load_dotenv(BASE_DIR / ".env")

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")


def generate_image(prompt, scene_number, story_context):

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        + ACCOUNT_ID
        + "/ai/run/"
        + MODEL
    )

    headers = {
        "Authorization": "Bearer " + API_TOKEN
    }

    full_prompt = (
        "Create a beautiful 2D cartoon illustration for a Hindi "
        "children's story, landscape 16:9 composition. "
        "Bright colors, expressive faces, polished children's "
        "storybook illustration, family-friendly. "
        "Maintain the same character designs, clothing, colors "
        "and proportions throughout this story. "
        "Do not replace human characters with animals. "
        "Do not add unrelated characters. "
        "Story context: "
        + story_context
        + " Current scene: "
        + prompt
    )

    payload = {
        "prompt": full_prompt,
        "steps": 4
    }

    for attempt in range(1, 4):

        try:
            print(
                f"Calling Cloudflare for scene {scene_number}, "
                f"attempt {attempt}/3..."
            )

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=180
            )

            if response.status_code in (401, 403):
                raise RuntimeError(
                    "Cloudflare authentication or permission error: "
                    + response.text[:1000]
                )

            if response.status_code == 429:
                raise RuntimeError(
                    "Cloudflare rate limit or free allowance reached. "
                    "Stopping image generation."
                )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if "image/" in content_type:
                image_bytes = response.content
            else:
                result = response.json()

                if not result.get("success", False):
                    raise RuntimeError(
                        "Cloudflare image generation failed: "
                        + str(result.get("errors", []))
                    )

                image_data = (
                    result.get("result", {}).get("image")
                )

                if not image_data:
                    raise RuntimeError(
                        "No image returned by Cloudflare."
                    )

                image_bytes = base64.b64decode(image_data)

            image = Image.open(
                BytesIO(image_bytes)
            ).convert("RGB")

            image = ImageOps.fit(
                image,
                (WIDTH, HEIGHT),
                method=Image.Resampling.LANCZOS
            )

            return image

        except RuntimeError:
            raise

        except requests.RequestException as error:

            if attempt == 3:
                raise RuntimeError(
                    f"Scene {scene_number} image failed: {error}"
                )

            print("Temporary network error. Retrying...")
            time.sleep(attempt * 5)

        except Exception as error:
            raise RuntimeError(
                f"Could not process scene {scene_number}: {error}"
            )


def create_scene_images(story, output_dir=None):

    if not ACCOUNT_ID or not API_TOKEN:
        raise RuntimeError(
            "Cloudflare credentials missing from .env"
        )

    scenes = story.get("scenes", [])

    if len(scenes) != 12:
        raise ValueError(
            "Story must contain exactly 12 scenes."
        )

    target_dir = (
        Path(output_dir)
        if output_dir
        else IMAGE_DIR
    )

    target_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Build shared context from all scene descriptions.
    story_context = "Story title: " + story.get("title", "")

    for index, scene in enumerate(scenes, start=1):

        visual_prompt = scene.get("visual_prompt", "")

        if not visual_prompt:
            raise ValueError(
                f"Scene {index} has no visual_prompt."
            )

        story_context += (
            f"\nScene {index}: {visual_prompt}"
        )

    image_paths = []

    for index, scene in enumerate(scenes, start=1):

        print(
            f"\nGenerating AI story image {index}/12..."
        )

        visual_prompt = scene["visual_prompt"]

        image = generate_image(
            visual_prompt,
            index,
            story_context
        )

        image_path = (
            target_dir / f"scene_{index:02d}.png"
        )

        image.save(image_path, "PNG")

        image_paths.append(str(image_path))

        print("Saved:", image_path)

    print(
        "\nAll 12 Cloudflare AI story images generated!"
    )

    return image_paths
