
import os
import re
import json
import time
import math
import random
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
# LOCAL PROGRAMMED ANIMATION
# ==========================================

MODEL_NAME = "gemini-3.8-flash"
VOICE = "hi-IN-SwaraNeural"

WIDTH = 720
HEIGHT = 1280
FPS = 25

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

GEMINI_TIMEOUT_SECONDS = 300
MAX_STORY_ATTEMPTS = 3


# ==========================================
# HINDI FONT
# ==========================================

if platform.system() == "Windows":
    FONT_CANDIDATES = [
        Path(r"C:\Windows\Fonts\Nirmala.ttf"),
        Path(r"C:\Windows\Fonts\Nirmala.ttc"),
        Path(r"C:\Windows\Fonts\Arial.ttf"),
    ]
else:
    FONT_CANDIDATES = [
        Path(
            "/usr/share/fonts/truetype/noto/"
            "NotoSansDevanagari-Regular.ttf"
        ),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]

FONT_PATH = next(
    (path for path in FONT_CANDIDATES if path.exists()),
    None
)


# ==========================================
# REQUIREMENTS
# ==========================================

def check_requirements():
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Set it in PowerShell "
            "or GitHub Actions Secrets."
        )

    if FONT_PATH is None:
        raise FileNotFoundError(
            "Hindi font not found. Install Nirmala UI on Windows "
            "or fonts-noto-core on GitHub Actions."
        )

    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True,
        timeout=20
    )

    if result.returncode != 0:
        raise RuntimeError("FFmpeg is not working correctly.")


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


def get_font(size):
    return ImageFont.truetype(str(FONT_PATH), size)


# ==========================================
# GENERATE A HINDI CHILDREN'S STORY
# ==========================================

def generate_story():
    print(
        "\n1. Generating a new Hindi children's story...",
        flush=True
    )

    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={
            "timeout": GEMINI_TIMEOUT_SECONDS * 1000
        }
    )

    prompt = """
You are a creative Hindi children's story writer.

Create a NEW and original Hindi story for children aged 4 to 8.

Return ONLY valid JSON in this format:

{
  "title": "Hindi story title",
  "scenes": [
    {
      "narration": "Two or three complete Hindi sentences.",
      "visual": "Detailed English description of this scene."
    }
  ],
  "moral": "Short Hindi moral."
}

Requirements:
- Exactly 8 scenes.
- Use natural Hindi written in Devanagari.
- Each scene must have 2 or 3 complete sentences.
- Include a problem, a clever solution, and a happy ending.
- Invent different characters, animals, settings, and events.
- Do not always use the same child, squirrel, tree, or background.
- Each scene must describe a distinct visual moment.
- Keep character appearance consistent within the story.
- Describe colorful children's cartoon scenes and clear actions.
- Avoid famous copyrighted characters.
- Avoid repeated sentences and spelling mistakes.
- Return valid JSON only, without Markdown fences.
"""

    response = None

    for attempt in range(1, MAX_STORY_ATTEMPTS + 1):
        try:
            print(
                f"Gemini attempt {attempt}/{MAX_STORY_ATTEMPTS}",
                flush=True
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if response.text and response.text.strip():
                break

            raise RuntimeError("Gemini returned an empty response.")

        except Exception as error:
            print(f"Story attempt failed: {error}", flush=True)

            if attempt == MAX_STORY_ATTEMPTS:
                raise

            time.sleep(attempt * 10)

    story_text = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        response.text.strip(),
        flags=re.IGNORECASE
    )

    try:
        story = json.loads(story_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Gemini returned invalid JSON: {error}"
        ) from error

    if not isinstance(story.get("scenes"), list):
        raise RuntimeError("Story scenes are invalid.")

    if len(story["scenes"]) != 8:
        raise RuntimeError("The story must contain exactly 8 scenes.")

    if not story.get("title") or not story.get("moral"):
        raise RuntimeError("Story title or moral is missing.")

    for number, scene in enumerate(story["scenes"], start=1):
        if not scene.get("narration", "").strip():
            raise RuntimeError(
                f"Scene {number} has no narration."
            )

        if not scene.get("visual", "").strip():
            raise RuntimeError(
                f"Scene {number} has no visual description."
            )

    print("Story generated:", story["title"], flush=True)
    return story


# ==========================================
# TEXT HELPERS
# ==========================================

def wrap_text(draw, text, font, max_width):
    lines = []
    current = ""

    for word in text.split():
        candidate = word if not current else current + " " + word

        bounds = draw.textbbox(
            (0, 0),
            candidate,
            font=font
        )

        if bounds[2] - bounds[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


# ==========================================
# DRAW BACKGROUND
# ==========================================

def draw_gradient(draw, top, bottom):
    for y in range(HEIGHT):
        ratio = y / max(1, HEIGHT - 1)

        color = tuple(
            int(top[i] * (1 - ratio) + bottom[i] * ratio)
            for i in range(3)
        )

        draw.line(
            (0, y, WIDTH, y),
            fill=color
        )


# ==========================================
# DRAW ANIMATED CARTOON CHARACTER
# ==========================================

def draw_character(
    draw,
    x,
    y,
    scale,
    shirt,
    phase,
    action="normal"
):
    bob = int(math.sin(phase * 4) * 7 * scale)

    head_r = int(55 * scale)
    head_y = y - int(225 * scale) + bob

    skin = "#C98255"

    # Shadow
    draw.ellipse(
        (
            x - int(72 * scale),
            y - int(8 * scale),
            x + int(72 * scale),
            y + int(12 * scale)
        ),
        fill="#5B8B56"
    )

    # Moving legs
    swing = int(math.sin(phase * 5) * 17 * scale)

    hip_y = y - int(78 * scale) + bob

    draw.line(
        (
            x - int(18 * scale),
            hip_y,
            x - int(22 * scale) + swing,
            y - int(8 * scale)
        ),
        fill="#263B65",
        width=max(5, int(15 * scale))
    )

    draw.line(
        (
            x + int(18 * scale),
            hip_y,
            x + int(22 * scale) - swing,
            y - int(8 * scale)
        ),
        fill="#263B65",
        width=max(5, int(15 * scale))
    )

    # Body
    draw.rounded_rectangle(
        (
            x - int(48 * scale),
            y - int(185 * scale) + bob,
            x + int(48 * scale),
            y - int(70 * scale) + bob
        ),
        radius=int(18 * scale),
        fill=shirt,
        outline="#583B36",
        width=max(1, int(2 * scale))
    )

    # Arms
    arm_raise = (
        int(42 * scale)
        if action == "help"
        else int(math.sin(phase * 4) * 12 * scale)
    )

    draw.line(
        (
            x - int(42 * scale),
            y - int(165 * scale) + bob,
            x - int(70 * scale),
            y - int(112 * scale) + bob
        ),
        fill=skin,
        width=max(7, int(17 * scale))
    )

    draw.line(
        (
            x + int(42 * scale),
            y - int(165 * scale) + bob,
            x + int(70 * scale),
            y - int(125 * scale) - arm_raise + bob
        ),
        fill=skin,
        width=max(7, int(17 * scale))
    )

    # Head
    draw.ellipse(
        (
            x - head_r,
            head_y - head_r,
            x + head_r,
            head_y + head_r
        ),
        fill=skin,
        outline="#59392C",
        width=max(2, int(3 * scale))
    )

    # Hair
    draw.pieslice(
        (
            x - head_r - int(2 * scale),
            head_y - head_r - int(9 * scale),
            x + head_r + int(2 * scale),
            head_y + int(22 * scale)
        ),
        180,
        360,
        fill="#34241E"
    )

    # Eyes
    eye_y = head_y - int(2 * scale)

    draw.ellipse(
        (
            x - int(23 * scale),
            eye_y - int(5 * scale),
            x - int(12 * scale),
            eye_y + int(8 * scale)
        ),
        fill="#1F1F1F"
    )

    draw.ellipse(
        (
            x + int(12 * scale),
            eye_y - int(5 * scale),
            x + int(23 * scale),
            eye_y + int(8 * scale)
        ),
        fill="#1F1F1F"
    )

    # Smile
    draw.arc(
        (
            x - int(19 * scale),
            head_y + int(12 * scale),
            x + int(20 * scale),
            head_y + int(38 * scale)
        ),
        5,
        170,
        fill="#7D2F2F",
        width=max(2, int(3 * scale))
    )


# ==========================================
# DRAW TREE WITH MOVING LEAVES
# ==========================================

def draw_tree(draw, x, ground, scale, phase, bloom=False):
    sway = int(math.sin(phase * 2) * 8 * scale)

    draw.rectangle(
        (
            x - int(18 * scale),
            ground - int(190 * scale),
            x + int(18 * scale),
            ground
        ),
        fill="#80512E"
    )

    leaves = [
        (-42, -190, 52),
        (18, -230, 64),
        (65, -175, 50),
        (-8, -155, 54)
    ]

    for ox, oy, radius in leaves:
        xx = x + int(ox * scale) + sway
        yy = ground + int(oy * scale)

        draw.ellipse(
            (
                xx - int(radius * scale),
                yy - int(radius * scale),
                xx + int(radius * scale),
                yy + int(radius * scale)
            ),
            fill="#3E9B50",
            outline="#23733B",
            width=max(1, int(3 * scale))
        )

    if bloom:
        for ox, oy in [
            (-45, -205),
            (20, -250),
            (70, -180),
            (-5, -160),
            (35, -205)
        ]:
            xx = x + int(ox * scale) + sway
            yy = ground + int(oy * scale)

            draw.ellipse(
                (
                    xx - int(12 * scale),
                    yy - int(12 * scale),
                    xx + int(12 * scale),
                    yy + int(12 * scale)
                ),
                fill="#FFDB65"
            )


# ==========================================
# CREATE ONE ANIMATED FRAME
# ==========================================

def render_frame(
    story,
    scene,
    number,
    frame_number,
    scene_frames,
    output_path,
    seed
):
    phase = frame_number / FPS

    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    # Different sky colors for different scenes
    skies = [
        ((115, 196, 244), (224, 246, 255)),
        ((255, 190, 155), (255, 235, 190)),
        ((143, 190, 236), (225, 238, 255)),
        ((145, 220, 200), (230, 250, 218))
    ]

    top, bottom = skies[(number - 1) % len(skies)]
    draw_gradient(draw, top, bottom)

    # Sun
    sun_x = int(WIDTH * 0.78 + math.sin(phase * 0.3) * 15)

    draw.ellipse(
        (sun_x - 48, 95, sun_x + 48, 191),
        fill="#FFE66D"
    )

    # Moving clouds
    for i in range(3):
        cloud_x = int(
            (
                i * 300
                + frame_number * 0.7
                + number * 70
            ) % (WIDTH + 180) - 80
        )

        cloud_y = 160 + i * 75

        draw.ellipse(
            (
                cloud_x,
                cloud_y,
                cloud_x + 110,
                cloud_y + 36
            ),
            fill="#FFFFFF"
        )

        draw.ellipse(
            (
                cloud_x + 25,
                cloud_y - 20,
                cloud_x + 82,
                cloud_y + 40
            ),
            fill="#FFFFFF"
        )

    # Ground
    ground = int(HEIGHT * 0.77)

    draw.ellipse(
        (-150, ground - 130, WIDTH + 180, HEIGHT + 180),
        fill="#76C76B"
    )

    draw.rectangle(
        (0, ground, WIDTH, HEIGHT),
        fill="#59B85E"
    )

    # Flowers
    for i in range(10):
        flower_x = (i * 83 + number * 31) % WIDTH
        flower_y = ground + 45 + (i % 3) * 34

        draw.line(
            (
                flower_x,
                flower_y,
                flower_x,
                flower_y + 23
            ),
            fill="#287C3C",
            width=4
        )

        for petal in range(5):
            angle = petal * math.pi * 2 / 5

            px = flower_x + int(math.cos(angle) * 8)
            py = flower_y + int(math.sin(angle) * 8)

            draw.ellipse(
                (px - 5, py - 5, px + 5, py + 5),
                fill=["#FF76A8", "#FFDA59", "#C69BFF"][i % 3]
            )

    visual = scene["visual"].lower()

    # Scene-specific scenery
    if any(word in visual for word in [
        "tree", "forest", "garden", "plant", "flower", "magical"
    ]):
        draw_tree(
            draw,
            int(WIDTH * 0.72),
            ground + 10,
            0.78,
            phase,
            bloom=number >= 6
        )

    elif any(word in visual for word in [
        "house", "village", "home", "hut"
    ]):
        house_x = int(WIDTH * 0.69)
        house_y = ground - 150

        draw.rectangle(
            (
                house_x - 75,
                house_y,
                house_x + 75,
                ground
            ),
            fill="#F1B56B",
            outline="#8B5A35",
            width=3
        )

        draw.polygon(
            [
                (house_x - 95, house_y),
                (house_x, house_y - 100),
                (house_x + 95, house_y)
            ],
            fill="#D85B52"
        )

        draw.rectangle(
            (
                house_x - 20,
                ground - 70,
                house_x + 20,
                ground
            ),
            fill="#81502E"
        )

        draw.rectangle(
            (
                house_x - 58,
                house_y + 25,
                house_x - 18,
                house_y + 65
            ),
            fill="#9BE3F4"
        )

        draw.rectangle(
            (
                house_x + 20,
                house_y + 25,
                house_x + 58,
                house_y + 65
            ),
            fill="#9BE3F4"
        )

    elif any(word in visual for word in [
        "river", "water", "pond", "lake", "sea", "ocean"
    ]):
        water_y = ground - 45

        draw.rectangle(
            (0, water_y, WIDTH, water_y + 115),
            fill="#35A9E8"
        )

        for i in range(6):
            water_x = (
                i * 145 + int(frame_number * 2)
            ) % (WIDTH + 80) - 40

            draw.arc(
                (
                    water_x,
                    water_y + 25,
                    water_x + 75,
                    water_y + 55
                ),
                0,
                180,
                fill="#D5F6FF",
                width=3
            )

    elif any(word in visual for word in [
        "mountain", "snow", "ice"
    ]):
        draw.polygon(
            [
                (0, ground - 80),
                (150, ground - 350),
                (330, ground - 80)
            ],
            fill="#F2F6FC"
        )

        draw.polygon(
            [
                (220, ground - 80),
                (450, ground - 410),
                (690, ground - 80)
            ],
            fill="#D9E9F5"
        )

    elif any(word in visual for word in [
        "space", "planet", "rocket"
    ]):
        draw.rectangle(
            (0, 0, WIDTH, HEIGHT),
            fill="#17244F"
        )

        for i in range(55):
            star_x = (i * 97 + number * 23) % WIDTH
            star_y = (i * 71 + number * 19) % HEIGHT

            draw.ellipse(
                (
                    star_x,
                    star_y,
                    star_x + 3,
                    star_y + 3
                ),
                fill="#FFFFFF"
            )

        draw.ellipse(
            (
                WIDTH - 190,
                170,
                WIDTH - 50,
                310
            ),
            fill="#A98BFA"
        )

        draw.polygon(
            [
                (100, ground - 240),
                (145, ground - 120),
                (55, ground - 120)
            ],
            fill="#FF786E"
        )

        draw.rectangle(
            (
                80,
                ground - 175,
                120,
                ground - 90
            ),
            fill="#FFFFFF"
        )

    # Programmed character motion
    action = (
        "help"
        if any(word in visual for word in [
            "help", "water", "carry", "give",
            "save", "plant", "pick", "hold"
        ])
        else "normal"
    )

    character_x = int(
        WIDTH * 0.30
        + math.sin(phase * 2) * WIDTH * 0.035
        + (frame_number / max(1, scene_frames)) * 18
    )

    draw_character(
        draw,
        character_x,
        ground + 6,
        0.83,
        ["#3978D4", "#D94F70", "#7B61A8", "#E58B2A"][number % 4],
        phase,
        action
    )

    # Story title
    title_font = get_font(31)
    subtitle_font = get_font(27)

    draw.rounded_rectangle(
        (24, 24, WIDTH - 24, 95),
        radius=20,
        fill="#17233D"
    )

    title = story["title"]

    while (
        draw.textbbox((0, 0), title, font=title_font)[2] > WIDTH - 70
        and title_font.size > 20
    ):
        title_font = get_font(title_font.size - 2)

    draw.text(
        (WIDTH // 2, 59),
        title,
        font=title_font,
        fill="white",
        anchor="mm",
        stroke_width=1,
        stroke_fill="#253047"
    )

    # Hindi subtitles
    narration = scene["narration"].strip()

    lines = wrap_text(
        draw,
        narration,
        subtitle_font,
        WIDTH - 76
    )

    if len(lines) > 4:
        lines = lines[:3] + ["…"]

    box_height = max(118, len(lines) * 37 + 34)

    draw.rounded_rectangle(
        (
            22,
            HEIGHT - box_height - 25,
            WIDTH - 22,
            HEIGHT - 25
        ),
        radius=22,
        fill="#101827"
    )

    y = (
        HEIGHT - box_height - 25
        + (box_height - len(lines) * 37) // 2
    )

    for line in lines:
        draw.text(
            (WIDTH // 2, y),
            line,
            font=subtitle_font,
            fill="#FFFFFF",
            anchor="mm",
            stroke_width=1,
            stroke_fill="#101827"
        )

        y += 37

    image.save(output_path, quality=88)


# ==========================================
# HINDI VOICE
# ==========================================

async def create_voice(text, audio_path):
    tts = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%"
    )

    await asyncio.wait_for(
        tts.save(str(audio_path)),
        timeout=120
    )


# ==========================================
# CREATE VIDEO
# ==========================================

def create_video(story, folder, seed):
    print(
        "\n3. Creating locally animated vertical video...",
        flush=True
    )

    segments = []

    for number, scene in enumerate(story["scenes"], start=1):
        print(
            f"Creating animated scene {number}/8...",
            flush=True
        )

        audio_path = folder / f"voice_{number:02d}.mp3"
        segment_path = folder / f"segment_{number:02d}.mp4"

        print(
            f"Generating Hindi narration for scene {number}...",
            flush=True
        )

        asyncio.run(
            create_voice(
                scene["narration"],
                audio_path
            )
        )

        # Determine narration duration with FFprobe
        probe = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ],
            capture_output=True,
            text=True
        )

        try:
            duration = max(
                4.0,
                float(probe.stdout.strip()) + 0.25
            )
        except (ValueError, AttributeError):
            duration = 7.0

        scene_frames = int(duration * FPS)

        frames_dir = folder / f"frames_{number:02d}"
        frames_dir.mkdir(exist_ok=True)

        # Render the moving cartoon frames
        for frame_number in range(scene_frames):
            frame_path = frames_dir / f"frame_{frame_number:05d}.jpg"

            render_frame(
                story,
                scene,
                number,
                frame_number,
                scene_frames,
                frame_path,
                seed
            )

        # Combine frames and narration into a scene MP4
        run_command(
            [
                "ffmpeg",
                "-y",
                "-framerate", str(FPS),
                "-i", str(frames_dir / "frame_%05d.jpg"),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                "-movflags", "+faststart",
                str(segment_path)
            ],
            timeout=900
        )

        segments.append(segment_path)

    # Join all scene videos
    concat_path = folder / "concat.txt"

    with concat_path.open("w", encoding="utf-8") as file:
        for segment in segments:
            file.write(
                f"file '{segment.resolve().as_posix()}'\n"
            )

    final_video = folder / "daily_video.mp4"

    print("Combining scenes...", flush=True)

    run_command(
        [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_path),
            "-c", "copy",
            "-movflags", "+faststart",
            str(final_video)
        ]
    )

    if not final_video.exists() or final_video.stat().st_size == 0:
        raise RuntimeError("The final MP4 was not created.")

    return final_video


# ==========================================
# MAIN
# ==========================================

def main():
    print("=" * 55)
    print("KYA BACHE - LOCAL ANIMATED HINDI STORY VIDEO")
    print("=" * 55, flush=True)

    check_requirements()

    seed = int(time.time())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    folder = OUTPUT_DIR / timestamp
    folder.mkdir(parents=True, exist_ok=True)

    story = generate_story()

    story_json_path = folder / "story.json"
    story_text_path = folder / "story.txt"

    with story_json_path.open("w", encoding="utf-8") as file:
        json.dump(
            story,
            file,
            ensure_ascii=False,
            indent=2
        )

    with story_text_path.open("w", encoding="utf-8") as file:
        file.write(story["title"] + "\n\n")

        for number, scene in enumerate(story["scenes"], start=1):
            file.write(
                f"SCENE {number}: {scene['narration']}\n"
                f"VISUAL: {scene['visual']}\n\n"
            )

        file.write("MORAL: " + story["moral"] + "\n")

    video_path = create_video(story, folder, seed)

    print("\n" + "=" * 55)
    print("VIDEO CREATED SUCCESSFULLY!")
    print("=" * 55)
    print("Title:", story["title"])
    print("Video:", video_path)
    print("Story:", story_text_path)
    print(
        "Note: this uses programmed local animation, "
        "not AI-generated 3D character motion."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Process stopped by user.", flush=True)
        raise SystemExit(1)
    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        raise SystemExit(1)
