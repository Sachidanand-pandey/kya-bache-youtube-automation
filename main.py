
import os
import re
import json
import asyncio
import subprocess
import platform
import time
import sys
from pathlib import Path
from datetime import datetime

import edge_tts
from PIL import Image, ImageDraw, ImageFont
from google import genai

# ==========================================
# KYA BACHE - HINDI STORY VIDEO AUTOMATION
# ==========================================

MODEL_NAME = "gemini-3.8-flash"
VOICE = "hi-IN-SwaraNeural"

WIDTH = 1280
HEIGHT = 720
FPS = 25

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

GEMINI_TIMEOUT_SECONDS = 300
TTS_TIMEOUT_SECONDS = 90
GEMINI_MAX_ATTEMPTS = 3

# Windows uses Nirmala; GitHub Actions Linux uses Noto Sans Devanagari.
if platform.system() == "Windows":
    FONT_PATH = Path(r"C:\Windows\Fonts\Nirmala.ttc")
else:
    FONT_PATH = Path(
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
    )


def check_requirements():
    """Check API key, font, and FFmpeg."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Configure it in your environment."
        )

    if not FONT_PATH.exists():
        raise FileNotFoundError(
            f"Hindi font not found: {FONT_PATH}"
        )

    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True,
        timeout=15
    )

    if result.returncode != 0:
        raise RuntimeError("FFmpeg is not working correctly.")


def generate_story():
    """Generate an original Hindi children's story with retries."""

    print("\n1. Generating Hindi story with Gemini...", flush=True)

    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={
            "timeout": GEMINI_TIMEOUT_SECONDS * 1000
        }
    )

    prompt = """
You are an experienced Hindi children's story writer.

Create a completely original Hindi story for children aged 4 to 8.

Return ONLY valid JSON in this structure:

{
  "title": "Hindi story title",
  "scenes": [
    {
      "narration": "Two or three complete Hindi sentences.",
      "visual": "Short English description of the illustration."
    }
  ],
  "moral": "Short Hindi moral."
}

Requirements:
- Exactly 8 scenes.
- Use natural, grammatically correct Hindi in Devanagari.
- Every scene should have 2 or 3 complete sentences.
- Keep the story suitable for a 1 to 2 minute video.
- Include a child and a friendly animal.
- Include a problem, a sensible solution, and a happy ending.
- Keep characters consistent.
- Give each scene a colorful cartoon illustration description.
- Avoid spelling mistakes and repeated sentences.
- Return JSON only, without Markdown fences.
"""

    response = None

    for attempt in range(1, GEMINI_MAX_ATTEMPTS + 1):
        try:
            print(
                f"Gemini request: attempt {attempt}/"
                f"{GEMINI_MAX_ATTEMPTS}",
                flush=True
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if not response.text or not response.text.strip():
                raise RuntimeError("Gemini returned an empty response.")

            break

        except Exception as error:
            print(
                f"Gemini attempt {attempt} failed: {error}",
                flush=True
            )

            if attempt == GEMINI_MAX_ATTEMPTS:
                raise

            wait_seconds = attempt * 15

            print(
                f"Retrying in {wait_seconds} seconds...",
                flush=True
            )

            time.sleep(wait_seconds)

    if response is None or not response.text:
        raise RuntimeError("Gemini did not return a story.")

    story_text = response.text.strip()

    # Remove optional Markdown JSON fences.
    story_text = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        story_text,
        flags=re.IGNORECASE
    )

    try:
        story = json.loads(story_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Gemini returned invalid JSON: {error}"
        ) from error

    if not isinstance(story.get("scenes"), list):
        raise RuntimeError("Gemini returned an invalid scenes list.")

    if len(story["scenes"]) != 8:
        raise RuntimeError(
            "Gemini must return exactly 8 scenes."
        )

    for index, scene in enumerate(story["scenes"], start=1):
        if not isinstance(scene, dict):
            raise RuntimeError(f"Scene {index} is invalid.")

        if not scene.get("narration", "").strip():
            raise RuntimeError(
                f"Scene {index} has no narration."
            )

        if not scene.get("visual", "").strip():
            scene["visual"] = "Colorful cartoon children's story scene"

    if not story.get("title") or not story.get("moral"):
        raise RuntimeError("The story title or moral is missing.")

    print("Story generated successfully.", flush=True)
    return story


def get_font(size):
    """Load the Hindi font."""

    return ImageFont.truetype(str(FONT_PATH), size)


def wrap_text(draw, text, font, max_width):
    """Wrap subtitles into lines."""

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = (
            word if not current_line
            else current_line + " " + word
        )

        box = draw.textbbox(
            (0, 0),
            test_line,
            font=font
        )

        if box[2] - box[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)

            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def draw_child(draw, x, y, scale=1.0):
    """Draw a simple cartoon child."""

    s = scale

    # Body
    draw.rounded_rectangle(
        (x - 35*s, y + 55*s, x + 35*s, y + 140*s),
        radius=int(12*s),
        fill="#3978D4"
    )

    # Legs
    draw.line(
        (x - 15*s, y + 135*s, x - 25*s, y + 185*s),
        fill="#283747",
        width=max(2, int(10*s))
    )

    draw.line(
        (x + 15*s, y + 135*s, x + 25*s, y + 185*s),
        fill="#283747",
        width=max(2, int(10*s))
    )

    # Face
    draw.ellipse(
        (x - 48*s, y - 45*s, x + 48*s, y + 55*s),
        fill="#F2C49B",
        outline="#8B5E3C",
        width=max(2, int(3*s))
    )

    # Hair
    draw.arc(
        (x - 48*s, y - 55*s, x + 48*s, y + 35*s),
        start=180,
        end=360,
        fill="#3B261B",
        width=max(3, int(15*s))
    )

    # Eyes
    for eye_x in (x - 15*s, x + 15*s):
        draw.ellipse(
            (eye_x - 4*s, y - 5*s, eye_x + 4*s, y + 5*s),
            fill="#222222"
        )

    # Smile
    draw.arc(
        (x - 20*s, y + 5*s, x + 20*s, y + 30*s),
        start=10,
        end=170,
        fill="#9C3D35",
        width=max(2, int(3*s))
    )


def draw_squirrel(draw, x, y, scale=1.0):
    """Draw a simple cartoon squirrel."""

    s = scale

    # Tail
    draw.ellipse(
        (x + 15*s, y - 65*s, x + 105*s, y + 30*s),
        fill="#B96732",
        outline="#75401E",
        width=max(2, int(3*s))
    )

    draw.ellipse(
        (x + 35*s, y - 45*s, x + 85*s, y + 5*s),
        fill="#F7C28B"
    )

    # Body
    draw.ellipse(
        (x - 20*s, y + 5*s, x + 50*s, y + 100*s),
        fill="#C8793D",
        outline="#75401E",
        width=max(2, int(3*s))
    )

    # Ears
    draw.polygon(
        [
            (x - 15*s, y + 5*s),
            (x - 25*s, y - 20*s),
            (x + 2*s, y + 2*s)
        ],
        fill="#C8793D"
    )

    draw.polygon(
        [
            (x + 25*s, y + 5*s),
            (x + 40*s, y - 20*s),
            (x + 45*s, y + 12*s)
        ],
        fill="#C8793D"
    )

    # Face
    draw.ellipse(
        (x - 25*s, y - 5*s, x + 45*s, y + 60*s),
        fill="#D88A4A",
        outline="#75401E",
        width=max(2, int(3*s))
    )

    # Eyes
    for eye_x in (x - 5*s, x + 20*s):
        draw.ellipse(
            (eye_x - 3*s, y + 15*s, eye_x + 4*s, y + 22*s),
            fill="#222222"
        )

    # Nose
    draw.ellipse(
        (x + 5*s, y + 30*s, x + 13*s, y + 38*s),
        fill="#5A3020"
    )


def create_scene_image(story, scene, index, folder):
    """Create a cartoon scene with Hindi subtitles."""

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        "#BCEBFF"
    )

    draw = ImageDraw.Draw(image)

    # Sky
    draw.ellipse((1010, 45, 1110, 145), fill="#FFD65A")

    draw.ellipse((100, 80, 210, 135), fill="white")
    draw.ellipse((145, 55, 245, 135), fill="white")
    draw.ellipse((190, 85, 285, 135), fill="white")

    # Hills and grass
    draw.ellipse((-200, 300, 550, 650), fill="#8AD47B")
    draw.ellipse((600, 320, 1450, 670), fill="#65BD69")
    draw.rectangle((0, 450, WIDTH, HEIGHT), fill="#72C96B")

    # Tree
    draw.rectangle(
        (900, 230, 965, 480),
        fill="#86512F"
    )

    draw.ellipse(
        (800, 135, 1060, 320),
        fill="#36964B"
    )

    draw.ellipse(
        (910, 100, 1150, 290),
        fill="#43A854"
    )

    # Characters
    draw_child(draw, 400, 290, 1.0)
    draw_squirrel(draw, 610, 370, 1.0)

    # Title
    title_font = get_font(35)

    draw.rounded_rectangle(
        (25, 15, WIDTH - 25, 72),
        radius=18,
        fill="white"
    )

    draw.text(
        (WIDTH // 2, 43),
        story["title"],
        font=title_font,
        fill="#263D64",
        anchor="mm"
    )

    # Subtitle background
    draw.rounded_rectangle(
        (35, 515, WIDTH - 35, 690),
        radius=22,
        fill="#14243A"
    )

    subtitle_font = get_font(30)

    lines = wrap_text(
        draw,
        scene["narration"].strip(),
        subtitle_font,
        WIDTH - 110
    )

    if len(lines) > 4:
        lines = lines[:3]
        lines.append("…")

    line_height = 39
    start_y = 600 - (len(lines) * line_height) // 2

    for line in lines:
        draw.text(
            (WIDTH // 2, start_y),
            line,
            font=subtitle_font,
            fill="white",
            anchor="mm"
        )

        start_y += line_height

    scene_path = folder / f"scene_{index:02d}.png"
    image.save(scene_path)

    return scene_path


async def create_voice(text, audio_path):
    """Generate Hindi narration using Edge TTS."""

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%"
    )

    await asyncio.wait_for(
        communicate.save(str(audio_path)),
        timeout=TTS_TIMEOUT_SECONDS
    )


def run_command(command, timeout=180):
    """Run FFmpeg and raise an error if it fails."""

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n" + result.stderr[-3000:]
        )


def create_video(story, folder):
    """Create narration, scene videos, and final MP4."""

    print(
        "\n3. Creating illustrations and video...",
        flush=True
    )

    segments = []

    for index, scene in enumerate(story["scenes"], start=1):
        print(
            f"Creating scene {index}/8...",
            flush=True
        )

        scene_image = create_scene_image(
            story,
            scene,
            index,
            folder
        )

        audio_path = folder / f"voice_{index:02d}.mp3"
        segment_path = folder / f"segment_{index:02d}.mp4"

        print(
            f"Generating Hindi narration for scene {index}...",
            flush=True
        )

        asyncio.run(
            create_voice(
                scene["narration"],
                audio_path
            )
        )

        print(
            f"Assembling scene {index}...",
            flush=True
        )

        run_command([
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-framerate", str(FPS),
            "-i", str(scene_image),
            "-i", str(audio_path),
            "-vf", "format=yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-shortest",
            "-movflags", "+faststart",
            str(segment_path)
        ])

        segments.append(segment_path)

    concat_path = folder / "concat.txt"

    with open(
        concat_path,
        "w",
        encoding="utf-8"
    ) as file:
        for segment in segments:
            safe_path = str(segment.resolve()).replace("\\", "/")
            file.write(f"file '{safe_path}'\n")

    final_video = folder / "daily_video.mp4"

    print(
        "\n4. Combining all scenes into the final video...",
        flush=True
    )

    run_command([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_path),
        "-c", "copy",
        "-movflags", "+faststart",
        str(final_video)
    ])

    if not final_video.exists() or final_video.stat().st_size == 0:
        raise RuntimeError("The final MP4 was not created correctly.")

    return final_video


def main():
    print("=" * 55)
    print("KYA BACHE - HINDI STORY VIDEO AUTOMATION")
    print("=" * 55, flush=True)

    check_requirements()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = OUTPUT_DIR / timestamp
    output_folder.mkdir(parents=True, exist_ok=True)

    story = generate_story()

    story_json_path = output_folder / "story.json"
    story_text_path = output_folder / "story.txt"

    with open(
        story_json_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            story,
            file,
            ensure_ascii=False,
            indent=2
        )

    with open(
        story_text_path,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(story["title"] + "\n\n")

        for index, scene in enumerate(story["scenes"], start=1):
            file.write(
                f"SCENE {index}: {scene['narration']}\n\n"
            )

        file.write(
            "MORAL: " + story["moral"] + "\n"
        )

    video_path = create_video(
        story,
        output_folder
    )

    print("\n" + "=" * 55)
    print("VIDEO CREATED SUCCESSFULLY!")
    print("=" * 55)
    print("Title:", story["title"])
    print("Video:", video_path)
    print("Story:", story_text_path)
    print("Output folder:", output_folder)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess stopped by user.", flush=True)
        sys.exit(1)
    except Exception as error:
        print(f"\nERROR: {error}", flush=True)
        sys.exit(1)
