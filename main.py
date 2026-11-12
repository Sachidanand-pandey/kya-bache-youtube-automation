import json
import shutil
import subprocess
from pathlib import Path

from story_generator import generate_story
from image_generator import create_scene_images
from audio_generator import generate_audio
from video_editor import render_video
from thumbnail_generator import make_thumbnail

OUTPUT = Path("output")

def main():
    OUTPUT.mkdir(exist_ok=True)
    for folder in ("images", "audio", "render"):
        path = OUTPUT / folder
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)

    story = generate_story()
    print("Story:", story["title"])
    print("Story source:", story.get("source"))

    images = create_scene_images(story)
    audio = generate_audio(story)
    video = render_video(images, audio)
    thumbnail = make_thumbnail(images[0], story["title"])

    metadata = {
        "title": story["title"] + " | Hindi Moral Story | Kya Bache",
        "description": (
            story["title"] + "\n\n" + story["moral"] +
            "\n\nबच्चों के लिए एक प्यारी हिंदी कहानी। ऐसी और कहानियों के लिए "
            "Kya Bache चैनल को सब्सक्राइब करें।\n\n"
            "#HindiKahani #MoralStories #KyaBache #KidsStories"
        ),
        "tags": ["Kya Bache", "Hindi Story", "Hindi Moral Story",
                 "Kids Story", "Hindi Kahani"],
        "category_id": "22",
        "made_for_kids": True,
        "story_source": story.get("source", "unknown"),
        "video": str(video),
        "thumbnail": str(thumbnail)
    }
    (OUTPUT / "upload_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (OUTPUT / "story.json").write_text(
        json.dumps(story, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 55)
    print("VIDEO GENERATION COMPLETED")
    print("Video:", video)
    print("Thumbnail:", thumbnail)
    print("Duration and resolution check:")
    subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=width,height", "-of", "default=noprint_wrappers=1",
        str(video)
    ], check=True)
    print("Review the video before enabling automatic public uploads.")

if __name__ == "__main__":
    main()
