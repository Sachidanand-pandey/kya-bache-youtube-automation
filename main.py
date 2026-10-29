
import os
import re
import json
import time
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

import edge_tts
from google import genai
from google.genai import types

# KYA BACHE - AI illustrated Hindi story videos.
# This creates AI scene images with camera movement,
# narration and optional music.
# It does NOT create full moving 3D character animation.

TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
VOICE = "hi-IN-SwaraNeural"

WIDTH = 720
HEIGHT = 1280
FPS = 25
SCENE_COUNT = 8

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
MUSIC_FILE = BASE_DIR / "music" / "background.mp3"

SUBSCRIBE_TEXT = (
    "ऐसी और मज़ेदार कहानियों के लिए "
    "हमारे चैनल को सब्सक्राइब करें।"
)


def run_command(command, timeout=900):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n" + result.stderr[-4000:]
        )


def check_requirements():
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY missing. Set it in your "
            "environment or GitHub Actions Secrets."
        )

    for cmd in ("ffmpeg", "ffprobe"):
        result = subprocess.run(
            [cmd, "-version"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"{cmd} is missing or not available on PATH."
            )

    if not MUSIC_FILE.exists():
        print(
            "NOTICE: music/background.mp3 not found; "
            "video will have narration without background music."
        )


def generate_story(client):
    prompt = f"""
Create an original Hindi children's story for ages 4-8.

Return only valid JSON:

{{
  "title": "Hindi title",
  "scenes": [
    {{
      "narration": "Two or three complete Hindi sentences.",
      "visual": "Detailed English visual description of every person, animal, object, action and setting in this scene."
    }}
  ],
  "moral": "Short Hindi moral."
}}

Requirements:
- Exactly {SCENE_COUNT} scenes.
- Natural Hindi in Devanagari.
- Beginning, problem, clever solution and happy ending.
- Different visual moment in every scene.
- Keep character appearance consistent across scenes.
- Describe every visible character and important object explicitly.
- Friendly cinematic 3D animated storybook style.
- No copyrighted characters, logos, text in image, or markdown.
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            print(
                f"Generating story (attempt {attempt}/3)...",
                flush=True
            )

            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt
            )

            raw = re.sub(
                r"^\s*```(?:json)?\s*|\s*```\s*$",
                "",
                (response.text or "").strip(),
                flags=re.I
            )

            story = json.loads(raw)

            if len(story.get("scenes", [])) != SCENE_COUNT:
                raise ValueError(
                    f"Story must have {SCENE_COUNT} scenes."
                )

            if not story.get("title") or not story.get("moral"):
                raise ValueError(
                    "Story title or moral is missing."
                )

            for scene in story["scenes"]:
                if not scene.get("narration") or not scene.get("visual"):
                    raise ValueError(
                        "A scene is missing narration or visual description."
                    )

            print(
                "Story:",
                story["title"],
                flush=True
            )

            return story

        except Exception as exc:
            last_error = exc

            print(
                "Story generation failed:",
                exc,
                flush=True
            )

            if attempt < 3:
                time.sleep(attempt * 5)

    raise RuntimeError(
        f"Could not generate story: {last_error}"
    )


def save_image_part(part, output_path):
    inline = getattr(part, "inline_data", None)

    if inline is None or not getattr(inline, "data", None):
        return False

    data = inline.data

    if isinstance(data, str):
        import base64
        data = base64.b64decode(data)

    output_path.write_bytes(data)

    return True


def generate_scene_image(client, story, scene, number, folder):
    image_path = folder / f"scene_{number:02d}.png"

    prompt = f"""
Create one polished vertical 9:16 image for a children's story
in a cinematic, high-quality 3D animated family-film style.

Use expressive faces, detailed materials, soft cinematic lighting,
rich colors, child-friendly composition.

Story title: {story['title']}

Scene visual: {scene['visual']}

Include EVERY person, animal, and important object explicitly
mentioned in this scene together in the image.

Do not replace an animal with a human and do not omit characters.

Keep character colors, clothing, and appearance consistent
with the description.

Show the action clearly.

No text, letters, logos, or watermark.
"""

    last_error = None

    for attempt in range(1, 3):
        try:
            print(
                f"Generating scene image {number}/{SCENE_COUNT}...",
                flush=True
            )

            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
            )

            for part in response.parts:
                if save_image_part(part, image_path):
                    return image_path

            raise RuntimeError(
                "No image returned. Verify image model access: "
                + IMAGE_MODEL
            )

        except Exception as exc:
            last_error = exc

            print(
                f"Image attempt {attempt} failed:",
                exc,
                flush=True
            )

            if attempt == 1:
                time.sleep(5)

    raise RuntimeError(
        f"Failed to generate scene {number}: {last_error}"
    )


async def create_voice(text, audio_path):
    tts = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%"
    )

    await asyncio.wait_for(
        tts.save(str(audio_path)),
        timeout=180
    )


def get_duration(audio_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    try:
        return max(
            4.0,
            float(result.stdout.strip()) + 0.4
        )

    except (ValueError, AttributeError):
        return 6.0


def make_scene_video(
    image_path,
    audio_path,
    video_path,
    duration
):
    frames = max(
        1,
        int(duration * FPS)
    )

    # Slow zoom makes the illustration feel less static.
    zoom_filter = (
        "zoompan=z='min(zoom+0.0005,1.08)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "format=yuv420p"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-framerate", str(FPS),
            "-i", str(image_path),
            "-i", str(audio_path),
            "-vf", zoom_filter,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-t", f"{duration:.2f}",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
            str(video_path)
        ],
        timeout=900
    )


def make_outro(client, folder):
    image_path = folder / "subscribe_outro.png"
    audio_path = folder / "subscribe_outro.mp3"
    video_path = folder / "subscribe_outro.mp4"

    prompt = """
Vertical 9:16 cheerful cinematic 3D animated
children's story ending image.

Friendly children and cute forest animals waving goodbye,
bright festive colors, warm lighting.

Leave clear empty space in center for a subscribe message.

No text, no logos, no watermark.
"""

    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        )
    )

    saved = False

    for part in response.parts:
        if save_image_part(part, image_path):
            saved = True
            break

    if not saved:
        raise RuntimeError(
            "No image returned for subscribe outro."
        )

    asyncio.run(
        create_voice(
            SUBSCRIBE_TEXT,
            audio_path
        )
    )

    duration = get_duration(audio_path)

    # Hindi subscribe message is spoken in the outro.
    run_command(
        [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-framerate", str(FPS),
            "-i", str(image_path),
            "-i", str(audio_path),
            "-vf",
            f"scale={WIDTH}:{HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},format=yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-t", f"{duration:.2f}",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
            str(video_path)
        ]
    )

    return video_path


def combine_videos(videos, final_path):
    concat_path = final_path.parent / "concat.txt"

    with concat_path.open(
        "w",
        encoding="utf-8"
    ) as handle:

        for video in videos:
            handle.write(
                f"file '{video.resolve().as_posix()}'\n"
            )

    if MUSIC_FILE.exists():

        # Background music is mixed quietly with narration.
        run_command(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_path),
                "-stream_loop", "-1",
                "-i", str(MUSIC_FILE),
                "-filter_complex",
                "[1:a]volume=0.12[m];"
                "[0:a][m]amix=inputs=2:"
                "duration=first:dropout_transition=2[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                str(final_path)
            ],
            timeout=1800
        )

    else:
        run_command(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_path),
                "-c", "copy",
                "-movflags", "+faststart",
                str(final_path)
            ],
            timeout=1800
        )


def main():
    print("=" * 60)
    print("KYA BACHE - AI ILLUSTRATED HINDI STORY VIDEO")
    print("=" * 60, flush=True)

    check_requirements()

    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"]
    )

    folder = OUTPUT_DIR / datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    story = generate_story(client)

    # Add spoken subscribe message to final story scene.
    story["scenes"][-1]["narration"] += (
        " " + SUBSCRIBE_TEXT
    )

    story_path = folder / "story.json"

    story_path.write_text(
        json.dumps(
            story,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    videos = []

    for number, scene in enumerate(
        story["scenes"],
        start=1
    ):

        image_path = generate_scene_image(
            client,
            story,
            scene,
            number,
            folder
        )

        audio_path = folder / f"voice_{number:02d}.mp3"

        video_path = folder / f"scene_video_{number:02d}.mp4"

        print(
            f"Creating Hindi narration for scene {number}...",
            flush=True
        )

        asyncio.run(
            create_voice(
                scene["narration"],
                audio_path
            )
        )

        make_scene_video(
            image_path,
            audio_path,
            video_path,
            get_duration(audio_path)
        )

        videos.append(video_path)

    videos.append(
        make_outro(
            client,
            folder
        )
    )

    final_path = folder / "daily_video.mp4"

    print(
        "Combining scenes and audio...",
        flush=True
    )

    combine_videos(
        videos,
        final_path
    )

    if (
        not final_path.exists()
        or final_path.stat().st_size == 0
    ):
        raise RuntimeError(
            "Final MP4 was not created."
        )

    print(
        "VIDEO CREATED:",
        final_path,
        flush=True
    )

    print(
        "Background music:",
        "included"
        if MUSIC_FILE.exists()
        else "not added; music file missing",
        flush=True
    )

    print(
        "Note: AI scene images plus camera zoom; "
        "not full character animation.",
        flush=True
    )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print(
            "Stopped by user.",
            flush=True
        )
        raise SystemExit(1)

    except Exception as exc:
        print(
            "ERROR:",
            exc,
            flush=True
        )
        raise SystemExit(1)
