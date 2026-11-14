
import os
import time
import base64
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image, ImageOps
from dotenv import load_dotenv


# --------------------------------------------------
# PROJECT SETTINGS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "output" / "images"

WIDTH = 1280
HEIGHT = 720

MODEL = "@cf/black-forest-labs/flux-1-schnell"

MAX_PROMPT_LENGTH = 2048
MAX_RETRIES = 3

load_dotenv(BASE_DIR / ".env")

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")


# --------------------------------------------------
# GENERATE ONE IMAGE
# --------------------------------------------------

def generate_image(prompt, scene_number, story_context):

    if not ACCOUNT_ID or not API_TOKEN:
        raise RuntimeError(
            "Cloudflare credentials missing from .env"
        )

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        + ACCOUNT_ID
        + "/ai/run/"
        + MODEL
    )

    headers = {
        "Authorization": "Bearer " + API_TOKEN
    }

    style_prompt = (
        "Create a beautiful 2D cartoon illustration for a "
        "Hindi children's story. Landscape 16:9 composition. "
        "Bright colors, expressive faces, polished children's "
        "storybook illustration, family-friendly. "
        "Maintain consistent character designs, clothing, "
        "colors and proportions. "
        "Do not replace human characters with animals. "
        "Do not add unrelated characters. "
    )

    # Keep the story context short.
    context = str(story_context)[:250]

    # Calculate remaining prompt space.
    available = (
        MAX_PROMPT_LENGTH
        - len(style_prompt)
        - len(context)
        - 2
    )

    if available <= 0:
        context = ""
        available = (
            MAX_PROMPT_LENGTH
            - len(style_prompt)
            - 1
        )

    scene_prompt = str(prompt)[:available]

    full_prompt = (
        style_prompt + context + " " + scene_prompt
    ).strip()

    # Final safety check.
    full_prompt = full_prompt[:MAX_PROMPT_LENGTH]

    payload = {
        "prompt": full_prompt,
        "steps": 4
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"Calling Cloudflare for scene {scene_number}, "
                f"attempt {attempt}/{MAX_RETRIES}..."
            )

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=180
            )

            # Authentication error.
            if response.status_code in (401, 403):
                raise RuntimeError(
                    "Cloudflare authentication or permission error: "
                    + response.text[:2000]
                )

            # Bad request. Do not retry.
            if response.status_code == 400:
                raise RuntimeError(
                    "Cloudflare returned 400 Bad Request: "
                    + response.text[:2000]
                )

            # Rate limit or free allowance issue.
            if response.status_code == 429:
                raise RuntimeError(
                    "Cloudflare rate limit or free allowance "
                    "reached. Stopping image generation. "
                    + response.text[:1000]
                )

            # Retry server errors.
            if response.status_code >= 500:
                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        "Cloudflare server error: "
                        + response.text[:2000]
                    )

                print("Cloudflare server error. Retrying...")
                time.sleep(attempt * 5)
                continue

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            )

            # Cloudflare may return image bytes directly.
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
                        "No image returned by Cloudflare. "
                        + str(result)[:1000]
                    )

                image_bytes = base64.b64decode(image_data)

            # Open and resize image.
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

            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Scene {scene_number} image failed "
                    f"after {MAX_RETRIES} attempts: {error}"
                )

            print(
                "Temporary network error. Retrying..."
            )

            time.sleep(attempt * 5)

        except Exception as error:

            raise RuntimeError(
                f"Could not process scene {scene_number}: {error}"
            )


# --------------------------------------------------
# GENERATE ALL 12 SCENE IMAGES
# --------------------------------------------------

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

    # Use only the story title as shared context.
    # Do not send all 12 scene descriptions in every request.
    story_context = (
        "Story title: " + story.get("title", "")
    )

    image_paths = []

    for index, scene in enumerate(scenes, start=1):

        print(
            f"\nGenerating AI story image {index}/12..."
        )

        visual_prompt = scene.get("visual_prompt", "")

        if not visual_prompt:
            raise ValueError(
                f"Scene {index} has no visual_prompt."
            )

        image = generate_image(
            visual_prompt,
            index,
            story_context
        )

        image_path = (
            target_dir / f"scene_{index:02d}.png"
        )

        image.save(
            image_path,
            "PNG"
        )

        image_paths.append(str(image_path))

        print("Saved:", image_path)

    print(
        "\nAll 12 Cloudflare AI story images generated!"
    )

    return image_paths


# --------------------------------------------------
# TEST ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    print("Cloudflare Image Generator")
    print("--------------------------")

    if not ACCOUNT_ID:
        print("ERROR: CLOUDFLARE_ACCOUNT_ID is missing.")

    elif not API_TOKEN:
        print("ERROR: CLOUDFLARE_API_TOKEN is missing.")

    else:
        print("Cloudflare credentials found.")
        print("Model:", MODEL)
        print("Image size:", WIDTH, "x", HEIGHT)
        print("Ready to generate story images.")
