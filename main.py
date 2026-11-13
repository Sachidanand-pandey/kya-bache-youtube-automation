
import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from story_generator import (
    generate_story,
    record_successful_story
)
from image_generator import create_scene_images
from audio_generator import generate_audio
from video_editor import render_video
from thumbnail_generator import create_thumbnail


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"

STORY_FILE = OUTPUT_DIR / "story.json"
VIDEO_FILE = OUTPUT_DIR / "daily_video.mp4"
THUMBNAIL_FILE = OUTPUT_DIR / "thumbnail.jpg"
METADATA_FILE = OUTPUT_DIR / "upload_metadata.json"


def load_existing_story():

    if not STORY_FILE.exists():
        raise FileNotFoundError(
            "No saved story found. Generate a new story first."
        )

    with open(STORY_FILE, "r", encoding="utf-8") as file:
        story = json.load(file)

    if len(story.get("scenes", [])) != 12:
        raise ValueError(
            "Saved story must contain exactly 12 scenes."
        )

    return story


def save_metadata(story):

    metadata = {
        "title": story["title"] + " | Hindi Kids Story",

        "description": (
            story["title"]
            + "\n\n"
            + story["moral"]
            + "\n\nA Hindi story for children."
        ),

        "tags": [
            "Hindi Kids Story",
            "Children Stories",
            "Hindi Moral Story",
            "Kya Bache"
        ],

        "category": "Education",

        "privacy": "public",

        "story_source": story.get("source", "groq"),

        "scene_count": len(story.get("scenes", []))
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as file:

        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\nUpload metadata created successfully.")


def main():

    parser = argparse.ArgumentParser(
        description="Kya Bache Children's Story Automation"
    )

    parser.add_argument(
        "--topic",
        default="",
        help="Optional story topic"
    )

    parser.add_argument(
        "--use-existing-story",
        action="store_true",
        help="Use the previously saved story"
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\n================================")
    print("KYA BACHE - VIDEO AUTOMATION")
    print("================================\n")

    # Step 1: Generate or load story.

    if args.use_existing_story:

        print("Loading existing story...")

        story = load_existing_story()

    else:

        print("Generating new children's story...")

        story = generate_story(args.topic)

    print("\nStory:", story["title"])

    # Validate story.

    if len(story.get("scenes", [])) != 12:
        raise RuntimeError(
            "Story must contain exactly 12 scenes."
        )

    # Step 2: Generate scene images.

    print("\nGenerating 12 cartoon images...")

    image_paths = create_scene_images(story)

    if len(image_paths) != 12:
        raise RuntimeError(
            "Image generation did not produce 12 images."
        )

    # Step 3: Generate Hindi narration.

    print("\nGenerating Hindi narration...")

    audio_paths = generate_audio(story)

    if not audio_paths:
        raise RuntimeError(
            "Audio generation failed."
        )

    # Step 4: Create video.

    print("\nRendering final video...")

    rendered_video = render_video(
        image_paths,
        audio_paths
    )

    if not VIDEO_FILE.exists():
        raise FileNotFoundError(
            "Final video was not created: " + str(VIDEO_FILE)
        )

    # Step 5: Generate thumbnail.

    print("\nGenerating YouTube thumbnail...")

    create_thumbnail(story)

    if not THUMBNAIL_FILE.exists():
        raise FileNotFoundError(
            "Thumbnail was not created: " + str(THUMBNAIL_FILE)
        )

    # Step 6: Create YouTube metadata.

    print("\nCreating upload metadata...")

    save_metadata(story)

    # Step 7: Save story history.

    if not args.use_existing_story:

        print("\nSaving story history...")

        record_successful_story(story)

    # Final status.

    print("\n================================")
    print("VIDEO AUTOMATION COMPLETED")
    print("================================")

    print("\nStory:", story["title"])
    print("Scenes:", len(story["scenes"]))
    print("Video:", VIDEO_FILE)
    print("Thumbnail:", THUMBNAIL_FILE)
    print("Metadata:", METADATA_FILE)

    print("\nYouTube upload was NOT started.")
    print("The GitHub Actions workflow handles YouTube upload.")


if __name__ == "__main__":
    main()
