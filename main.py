
import argparse
import json
import shutil
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
        "privacy": "private"
    }

    with open(
        METADATA_FILE, "w", encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=4
        )


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

    # Step 2: Generate AI images.
    print("\nGenerating 12 AI cartoon images...")

    image_paths = create_scene_images(story)

    if len(image_paths) != 12:
        raise RuntimeError("Image generation did not produce 12 images.")

    # Step 3: Generate audio.
    print("\nGenerating Hindi narration...")

    audio_paths = generate_audio(story)

    if len(audio_paths) != 13:
        raise RuntimeError(
            "Expected 13 audio files: 12 scenes and 1 moral."
        )

    # Step 4: Render video.
    print("\nRendering final video...")

    # Keep the previous successful video safe.
    backup_video = OUTPUT_DIR / "previous_successful_video.mp4"

    if VIDEO_FILE.exists():
        shutil.copy2(VIDEO_FILE, backup_video)

    try:
        rendered_video = render_video(
            image_paths,
            audio_paths
        )

        if not Path(rendered_video).is_file():
            raise RuntimeError("Final video was not created.")

        if Path(rendered_video).stat().st_size == 0:
            raise RuntimeError("Final video is empty.")

    except Exception:

        if backup_video.exists():
            shutil.copy2(backup_video, VIDEO_FILE)

        raise

    # Step 5: Generate thumbnail.
    print("\nGenerating thumbnail...")

    create_thumbnail(story)

    # Step 6: Save metadata.
    save_metadata(story)

    # Step 7: Update history only after successful video creation.
    if not args.use_existing_story:
        record_successful_story(story)

    print("\n================================")
    print("VIDEO GENERATION SUCCESSFUL")
    print("================================")

    print("\nVideo:", VIDEO_FILE)
    print("Thumbnail:", THUMBNAIL_FILE)
    print("Metadata:", METADATA_FILE)

    print(
        "\nYouTube upload was NOT started."
        "\nPlease review the video before uploading."
    )


if __name__ == "__main__":
    main()
