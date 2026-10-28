
import os
import re
import json
import asyncio
import subprocess
import platform
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

# Use the correct Hindi font for each operating system.
if platform.system() == "Windows":
    FONT_PATH = Path(r"C:\Windows\Fonts\Nirmala.ttc")
else:
    FONT_PATH = Path(
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
    )

GEMINI_TIMEOUT_SECONDS = 300
TTS_TIMEOUT_SECONDS = 60


def check_requirements():
    """Check API key, Hindi font, and FFmpeg."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Configure it in your environment."
        )

    if not FONT_PATH.exists():
        raise FileNotFoundError(
            f"Hindi font not found: {FONT_PATH}. "
            "Install a Hindi-compatible font on this system."
        )

    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError("FFmpeg is not working correctly.")


def generate_story():
    """Generate an original Hindi children's story using Gemini."""

    print("\n1. Generating Hindi story with Gemini...", flush=True)

    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={"timeout": GEMINI_TIMEOUT_SECONDS * 1000}
    )

    prompt = """
You are an experienced Hindi children's story writer.

Create a completely original story for children aged 4 to 8.

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
- Each scene should have 2 or 3 complete sentences.
- Keep the total narration suitable for 1 to 2 minutes.
- Include a child and a friendly animal.
- Include a problem, a sensible solution and a happy ending.
- Keep the characters consistent throughout.
- Describe a colorful cartoon illustration for every scene.
- Avoid spelling mistakes and repeated sentences.
- Return JSON only, with no Markdown fences.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text or not response.text.strip():
        raise RuntimeError("Gemini returned an empty response.")

    story_text = response.text.strip()
    story_text = re.sub(
        r"^\`\`\`(?:json)?\s*|\s*\`\`\`$",
        "",
        story_text,
        flags=re.IGNORECASE
    )

    story = json.loads(story_text)

    if not isinstance(story.get("scenes"), list):
        raise RuntimeError("Gemini returned an invalid scenes list.")

    if len(story["scenes"]) != 8:
        raise RuntimeError(
            "Gemini must return exactly 8 scenes. Please run again."
        )

    for index, scene in enumerate(story["scenes"], start=1):
        if not scene.get("narration", "").strip():
            raise RuntimeError(f"Scene {index} has no narration.")

    if not story.get("title") or not story.get("moral"):
        raise RuntimeError("The title or moral is missing.")

    print("Story generated successfully.", flush=True)
    return story


def get_font(size):
    """Load the Hindi font."""

    return ImageFont.truetype(str(FONT_PATH), size)


def wrap_text(draw, text, font, max_width):
    """Wrap Hindi subtitles into lines."""

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = (
            word if not current_line
            else current_line + " " + word
        )

        box = draw.textbbox((0, 0), test_line, font=font)

        if box[2] - box[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def draw_child(draw, x, y, scale=1):
    """Draw a simple cartoon child."""

    width = max(2, int(3 * scale))

    # Body
    draw.rounded_rectangle(
        (
            x - 35 * scale, y + 55 * scale,
            x + 35 * scale, y + 140 * scale
        ),
        radius=int(12 * scale),
        fill="#3978D4"
    )

    # Legs
    draw.line(
        (
            x - 15 * scale, y + 135 * scale,
            x - 25 * scale, y + 185 * scale
        ),
        fill="#283747",
        width=int(10 * scale)
    )

    draw.line(
        (
            x + 15 * scale, y + 135 * scale,
            x + 25 * scale, y + 185 * scale
        ),
        fill="#283747",
        width=int(10 * scale)
    )

    # Face
    draw.ellipse(
        (
            x - 48 * scale, y - 45 * scale,
            x + 48 * scale, y + 55 * scale
        ),
        fill="#F2C49B",
        outline="#8B5E3C",
        width=width
    )

    # Hair
    draw.arc(
        (
            x - 48 * scale, y - 55 * scale,
            x + 48 * scale, y + 35 * scale
        ),
        start=180,
        end=360,
        fill="#3B261B",
        width=max(4, int(15 * scale))
    )

    # Eyes
    for eye_x in (x - 15 * scale, x + 15 * scale):
        draw.ellipse(
            (
                eye_x - 4 * scale, y - 5 * scale,
                eye_x + 4 * scale, y + 5 * scale
            ),
            fill="#222222"
        )

    # Smile
    draw.arc(
        (
            x - 20 * scale, y + 5 * scale,
            x + 20 * scale, y + 30 * scale
        ),
        start=10,
        end=170,
        fill="#9C3D35",
        width=3
    )


def draw_squirrel(draw, x, y, scale=1):
    """Draw a simple cartoon squirrel."""

    width = max(2, int(3 * scale))

    # Tail
    draw.ellipse(
        (
            x + 15 * scale, y - 65 * scale,
            x + 105 * scale, y + 30 * scale
        ),
        fill="#B96732",
        outline="#75401E",
        width=width
    )

    draw.ellipse(
        (
            x + 35 * scale, y - 45 * scale,
            x + 85 * scale, y + 5 * scale
        ),
        fill="#F7C28B"
    )

    # Body
    draw.ellipse(
        (
            x - 20 * scale, y + 5 * scale,
            x + 50 * scale, y + 100 * scale
        ),
        fill="#C8793D",
        outline="#75401E",
        width=width
    )

    # Ears
    draw.polygon(
        [
            (x - 15 * scale, y + 5 * scale),
            (x - 25 * scale, y - 20 * scale),
            (x + 2 * scale, y + 2 * scale)
        ],
        fill="#C8793D"
    )

    draw.polygon(
        [
            (x + 25 * scale, y + 5 * scale),
            (x + 40 * scale, y - 20 * scale),
            (x + 45 * scale, y + 12 * scale)
        ],
        fill="#C8793D"
    )

    # Face
    draw.ellipse(
        (
            x - 25 * scale, y - 5 * scale,
            x + 45 * scale, y + 60 * scale
        ),
        fill="#D88A4A",
        outline="#75401E",
        width=width
    )

    # Eyes
    for eye_x in (x - 5 * scale, x + 20 * scale):
        draw.ellipse(
            (
                eye_x - 3 * scale, y + 15 * scale,
                eye_x + 4 * scale, y + 22 * scale
            ),
            fill="#222222"
        )

    # Nose
    draw.ellipse(
        (
            x + 5 * scale, y + 30 * scale,
            x + 13 * scale, y + 38 * scale
        ),
        fill="#5A3020"
    )


def create_scene_image(story, scene, index, folder):
    """Draw a colorful cartoon scene and Hindi subtitles."""

    image = Image.new("RGB", (WIDTH, HEIGHT), "#BCEBFF")
    draw = ImageDraw.Draw(image)

    # Sun and clouds
    draw.ellipse((1010, 45, 1110, 145), fill="#FFD65A")
    draw.ellipse((100, 80, 210, 135), fill="white")
    draw.ellipse((145, 55, 245, 135), fill="white")
    draw.ellipse((190, 85, 285, 135), fill="white")

    # Background hills
    draw.ellipse((-200, 300, 550, 650), fill="#8AD47B")
    draw.ellipse((600, 320, 1450, 670), fill="#65BD69")

    # Grass
    draw.rectangle((0, 450, WIDTH, HEIGHT), fill="#72C96B")

    # Tree
    draw.rectangle((900, 230, 965, 480), fill="#86512F")
    draw.ellipse((800, 135, 1060, 320), fill="#36964B")
    draw.ellipse((910, 100, 1150, 290), fill="#43A854")

    # Characters
    draw_child(draw, 400, 290, 1.0)
    draw_squirrel(draw, 610, 370, 1.0)

    # Title banner
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

    # Subtitle banner
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
    """Create Hindi speech using Edge TTS."""

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%"
    )

    await asyncio.wait_for(
        communicate.save(str(audio_path)),
        timeout=TTS_TIMEOUT_SECONDS
    )


def run_command(command):
    """Run an external command and report failures."""

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=180
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg command failed:\n" + result.stderr[-3000:]
        )


def create_video(story, folder):
    """Create narration clips and combine them into an MP4."""

    print("\n3. Creating illustrations and video...", flush=True)
    segments = []

    for index, scene in enumerate(story["scenes"], start=1):
        print(f"Creating scene {index}/8...", flush=True)

        scene_image = create_scene_image(
            story, scene, index, folder
        )

        audio_path = folder / f"voice_{index:02d}.mp3"
        segment_path = folder / f"segment_{index:02d}.mp4"

        print(
            f"Generating Hindi voice for scene {index}...",
            flush=True
        )

        asyncio.run(
            create_voice(scene["narration"], audio_path)
        )

        print(f"Assembling scene {index}...", flush=True)

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

    with open(concat_path, "w", encoding="utf-8") as file:
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

    with open(story_json_path, "w", encoding="utf-8") as file:
        json.dump(story, file, ensure_ascii=False, indent=2)

    with open(story_text_path, "w", encoding="utf-8") as file:
        file.write(story["title"] + "\n\n")

        for index, scene in enumerate(story["scenes"], start=1):
            file.write(
                f"SCENE {index}: {scene['narration']}\n\n"
            )

        file.write("MORAL: " + story["moral"] + "\n")

    video_path = create_video(story, output_folder)

    print("\n" + "=" * 55)
    print("VIDEO CREATED SUCCESSFULLY!")
    print("=" * 55)
    print("Title:", story["title"])
    print("Video:", video_path)
    print("Story:", story_text_path)
    print("Output folder:", output_folder)
    print("\nOpen the MP4 and check the Hindi audio and subtitles.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as error:
        print("\nERROR:", error)
        print(
            "Check the error above, your API key, internet connection, "
            "installed packages, and FFmpeg."
        )
