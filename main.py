import json
import shutil
import subprocess
from pathlib import Path

from story_generator import generate_story, validate_story
from image_generator import create_scene_images
from audio_generator import generate_audio
from video_editor import render_video
from thumbnail_generator import make_thumbnail

OUTPUT = Path("output")


def main():
    OUTPUT.mkdir(exist_ok=True)

    # Generate and validate the story BEFORE deleting or creating video assets.
    story = validate_story(generate_story())
    if story.get("source") != "gemini":
        raise RuntimeError("Only a newly generated Gemini story can be rendered.")

    # Remove old outputs so a failed run can never leave a stale video to upload.
    for filename in ("daily_video.mp4", "daily_short.mp4", "thumbnail.jpg", "upload_metadata.json"):
        path = OUTPUT / filename
        if path.exists():
            path.unlink()
    for folder in ("images", "audio", "render"):
        path = OUTPUT / folder
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)

    print("Story:", story["title"])
    print("Story source:", story["source"])

    images = create_scene_images(story)
    if len(images) != 12:
        raise RuntimeError(f"Expected 12 scene images, got {len(images)}.")

    audio = generate_audio(story)
    if len(audio) != 13:  # 12 scenes plus the moral narration
        raise RuntimeError(f"Expected 13 audio files, got {len(audio)}.")

    video = render_video(images, audio)
    if not video.exists() or video.stat().st_size == 0:
        raise RuntimeError("Video rendering failed or produced an empty file.")

    thumbnail = make_thumbnail(images[0], story["title"])
    metadata = {
        "title": story["title"] + " | बाल हनुमान जी की कहानी | Kya Bache",
        "description": (
            story["title"] + "\n\n" + story["moral"] +
            "\n\nबाल हनुमान जी की एक नई, प्यारी हिंदी कहानी।\n"
            "बच्चों के लिए भक्ति, साहस और मदद की सीख।\n\n"
            "#BalHanuman #HindiKahani #KidsStories #KyaBache"
        ),
        "tags": ["Kya Bache", "Bal Hanuman", "बाल हनुमान", "Hindi Kids Story", "Hindi Moral Story"],
        "category_id": "22",
        "made_for_kids": True,
        "story_source": story["source"],
        "scene_count": len(story["scenes"]),
        "video": str(video),
        "thumbnail": str(thumbnail),
    }
    (OUTPUT / "upload_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("VIDEO GENERATION COMPLETED")
    print("Video:", video)
    print("Thumbnail:", thumbnail)
    subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=width,height", "-of", "default=noprint_wrappers=1",
        str(video)
    ], check=True)
    print("Review the generated video before allowing public uploads.")


if __name__ == "__main__":
    main()
