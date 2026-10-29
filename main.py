
import os
import math
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ==========================================
# KYA BACHE - FREE VIDEO GENERATOR
# ==========================================

WIDTH = 720
HEIGHT = 1280
FPS = 25
VOICE = "hi-IN-SwaraNeural"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
MUSIC_FILE = BASE_DIR / "music" / "background.mp3"

STORY = [
    {
        "text": "एक सुंदर जंगल में मोहन नाम का प्यारा बच्चा रहता था। उसे पक्षियों से बहुत प्यार था।",
        "kind": "forest"
    },
    {
        "text": "एक दिन मोहन को एक छोटी नीली चिड़िया मिली। चिड़िया उदास थी और उड़ नहीं पा रही थी।",
        "kind": "bird"
    },
    {
        "text": "मोहन ने प्यार से चिड़िया को उठाया और उसे थोड़ा पानी पिलाया।",
        "kind": "water"
    },
    {
        "text": "एक सफेद खरगोश भी वहाँ आया। दोनों ने मिलकर चिड़िया की मदद की।",
        "kind": "rabbit"
    },
    {
        "text": "कुछ देर बाद चिड़िया खुश हो गई और उसने अपने सुंदर नीले पंख फैलाए।",
        "kind": "happy"
    },
    {
        "text": "चिड़िया धीरे-धीरे आसमान में उड़ने लगी। मोहन और खरगोश बहुत खुश हुए।",
        "kind": "fly"
    },
    {
        "text": "चिड़िया वापस आई और मोहन के लिए एक सुंदर फूल लेकर आई।",
        "kind": "flower"
    },
    {
        "text": "मोहन ने सीखा कि हमें हमेशा दूसरों की मदद करनी चाहिए और जानवरों से प्यार करना चाहिए।",
        "kind": "ending"
    }
]

SUBSCRIBE_MESSAGE = (
    "ऐसी और मज़ेदार कहानियों के लिए हमारे चैनल को सब्सक्राइब करें। "
    "वीडियो अच्छी लगी हो तो लाइक करें। धन्यवाद!"
)


# ==========================================
# COMMAND HELPERS
# ==========================================

def run_command(command, timeout=1200):
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


def check_tools():
    for tool in ("ffmpeg", "ffprobe"):
        result = subprocess.run(
            [tool, "-version"],
            capture_output=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"{tool} is not installed or not in PATH."
            )


# ==========================================
# FONTS
# ==========================================

def get_font(size, bold=False):
    if os.name == "nt":
        fonts = [
            r"C:\Windows\Fonts\NirmalaB.ttf"
            if bold else r"C:\Windows\Fonts\Nirmala.ttf",
            r"C:\Windows\Fonts\arialbd.ttf"
            if bold else r"C:\Windows\Fonts\arial.ttf"
        ]
    else:
        fonts = [
            "/usr/share/fonts/truetype/noto/"
            + ("NotoSansDevanagari-Bold.ttf"
               if bold else "NotoSansDevanagari-Regular.ttf"),
            "/usr/share/fonts/truetype/dejavu/"
            + ("DejaVuSans-Bold.ttf"
               if bold else "DejaVuSans.ttf")
        ]

    for font_path in fonts:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                pass

    return ImageFont.load_default()


def centered_text(draw, text, y, font, color):
    box = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=color)


# ==========================================
# DRAW CARTOON CHARACTERS
# ==========================================

def draw_background(draw):
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill="#8ED8FF")

    draw.ellipse((535, 80, 650, 195), fill="#FFD64A")

    draw.ellipse((-160, 470, 430, 1000), fill="#66BD69")
    draw.ellipse((260, 480, 900, 1050), fill="#319B53")

    draw.rectangle((0, 820, WIDTH, HEIGHT), fill="#4DA957")

    for x, y in [(45, 570), (590, 560)]:
        draw.rectangle(
            (x + 32, y + 80, x + 60, y + 230),
            fill="#80502B"
        )
        draw.ellipse(
            (x, y, x + 100, y + 130),
            fill="#238646"
        )


def draw_boy(draw, x, y, scale=1.0):
    s = scale

    def box(values):
        return tuple(int(v * s) for v in values)

    draw.ellipse(
        (x, y, x + 95*s, y + 95*s),
        fill="#F4BD87"
    )
    draw.pieslice(
        (x - 3*s, y - 15*s, x + 100*s, y + 65*s),
        180, 360,
        fill="#51311F"
    )

    for ex in (x + 28*s, x + 67*s):
        draw.ellipse(
            (ex, y + 38*s, ex + 9*s, y + 48*s),
            fill="#222222"
        )

    draw.arc(
        (x + 32*s, y + 48*s, x + 68*s, y + 75*s),
        0, 180,
        fill="#9C3B35",
        width=max(2, int(3*s))
    )

    draw.rounded_rectangle(
        box((x - 5, y + 92, x + 100, y + 235)),
        radius=max(5, int(15*s)),
        fill="#F04C4C"
    )

    draw.line(
        (x + 5*s, y + 120*s, x - 35*s, y + 180*s),
        fill="#F4BD87",
        width=max(7, int(16*s))
    )
    draw.line(
        (x + 90*s, y + 120*s, x + 130*s, y + 180*s),
        fill="#F4BD87",
        width=max(7, int(16*s))
    )

    draw.line(
        (x + 25*s, y + 230*s, x + 15*s, y + 300*s),
        fill="#244D9A",
        width=max(8, int(20*s))
    )
    draw.line(
        (x + 72*s, y + 230*s, x + 82*s, y + 300*s),
        fill="#244D9A",
        width=max(8, int(20*s))
    )


def draw_bird(draw, x, y, scale=1.0):
    s = scale

    draw.ellipse(
        (x, y, x + 115*s, y + 80*s),
        fill="#2188F5"
    )
    draw.ellipse(
        (x + 20*s, y + 15*s, x + 80*s, y + 70*s),
        fill="#61BCFF"
    )
    draw.ellipse(
        (x + 70*s, y - 25*s, x + 135*s, y + 40*s),
        fill="#2188F5"
    )

    draw.ellipse(
        (x + 110*s, y - 5*s, x + 122*s, y + 7*s),
        fill="white"
    )
    draw.ellipse(
        (x + 114*s, y - 2*s, x + 120*s, y + 4*s),
        fill="#222222"
    )

    draw.polygon(
        [
            (x + 132*s, y + 5*s),
            (x + 158*s, y + 14*s),
            (x + 132*s, y + 23*s)
        ],
        fill="#FFB52E"
    )

    draw.polygon(
        [
            (x + 5*s, y + 30*s),
            (x - 28*s, y + 3*s),
            (x - 20*s, y + 48*s)
        ],
        fill="#1664C6"
    )


def draw_rabbit(draw, x, y, scale=1.0):
    s = scale

    draw.ellipse(
        (x + 10*s, y - 75*s, x + 40*s, y + 20*s),
        fill="white"
    )
    draw.ellipse(
        (x + 50*s, y - 85*s, x + 80*s, y + 20*s),
        fill="white"
    )
    draw.ellipse(
        (x, y + 45*s, x + 110*s, y + 145*s),
        fill="white"
    )
    draw.ellipse(
        (x + 15*s, y, x + 100*s, y + 90*s),
        fill="white"
    )

    draw.ellipse(
        (x + 35*s, y + 28*s, x + 44*s, y + 38*s),
        fill="#222222"
    )
    draw.ellipse(
        (x + 72*s, y + 28*s, x + 81*s, y + 38*s),
        fill="#222222"
    )
    draw.ellipse(
        (x + 56*s, y + 45*s, x + 65*s, y + 54*s),
        fill="#F18AA2"
    )


# ==========================================
# CREATE SCENE IMAGES
# ==========================================

def create_scene_image(scene, number, folder):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    draw_background(draw)

    kind = scene["kind"]

    if kind == "forest":
        draw_boy(draw, 250, 620, 1.05)
        draw_bird(draw, 475, 640, 0.8)

    elif kind == "bird":
        draw_boy(draw, 100, 650, 0.9)
        draw_bird(draw, 430, 710, 1.0)

    elif kind == "water":
        draw_boy(draw, 100, 650, 0.9)
        draw_bird(draw, 430, 735, 0.8)
        draw.ellipse((400, 835, 520, 875), fill="#72D8FF")

    elif kind == "rabbit":
        draw_boy(draw, 50, 650, 0.8)
        draw_bird(draw, 310, 720, 0.7)
        draw_rabbit(draw, 510, 770, 0.8)

    elif kind == "happy":
        draw_boy(draw, 70, 650, 0.85)
        draw_bird(draw, 410, 620, 0.95)
        draw_rabbit(draw, 520, 790, 0.65)

    elif kind == "fly":
        draw_boy(draw, 75, 660, 0.9)
        draw_bird(draw, 455, 350, 0.9)
        draw_rabbit(draw, 510, 800, 0.65)

    elif kind == "flower":
        draw_boy(draw, 80, 650, 0.85)
        draw_bird(draw, 415, 640, 0.85)

        fx, fy = 550, 880
        draw.line(
            (fx, fy, fx, fy + 65),
            fill="#24863D",
            width=7
        )

        for angle in range(0, 360, 60):
            a = math.radians(angle)
            cx = fx + int(15 * math.cos(a))
            cy = fy + int(15 * math.sin(a))
            draw.ellipse(
                (cx - 10, cy - 10, cx + 10, cy + 10),
                fill="#FF77B7"
            )

        draw.ellipse(
            (fx - 8, fy - 8, fx + 8, fy + 8),
            fill="#FFD447"
        )

    else:
        draw_boy(draw, 70, 650, 0.85)
        draw_bird(draw, 415, 620, 0.9)
        draw_rabbit(draw, 510, 800, 0.65)

    draw.rounded_rectangle(
        (25, 30, WIDTH - 25, 150),
        radius=24,
        fill="#173A6C",
        outline="white",
        width=3
    )

    centered_text(
        draw,
        "कहानी का मज़ेदार सफर",
        48,
        get_font(31, True),
        "white"
    )

    centered_text(
        draw,
        f"दृश्य {number}",
        95,
        get_font(23),
        "#FFE47A"
    )

    draw.rounded_rectangle(
        (25, 1000, WIDTH - 25, 1210),
        radius=24,
        fill="#173A6C",
        outline="white",
        width=3
    )

    font = get_font(25)
    words = scene["text"].split()
    lines = []
    current = ""

    for word in words:
        test = current + " " + word if current else word
        bbox = draw.textbbox((0, 0), test, font=font)

        if bbox[2] - bbox[0] > WIDTH - 80:
            if current:
                lines.append(current)
            current = word
        else:
            current = test

    if current:
        lines.append(current)

    y = 1025
    for line in lines[:4]:
        centered_text(draw, line, y, font, "white")
        y += 40

    path = folder / f"scene_{number:02d}.png"
    image.save(path)

    return path


# ==========================================
# CREATE SUBSCRIBE OUTRO IMAGE
# ==========================================

def create_outro_image(path):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#173A6C")
    draw = ImageDraw.Draw(image)

    draw_background(draw)
    draw_boy(draw, 65, 650, 0.8)
    draw_bird(draw, 445, 650, 0.9)
    draw_rabbit(draw, 500, 850, 0.6)

    draw.rounded_rectangle(
        (30, 300, WIDTH - 30, 590),
        radius=32,
        fill="#13294B",
        outline="white",
        width=4
    )

    centered_text(
        draw,
        "कहानी अच्छी लगी?",
        330,
        get_font(38, True),
        "white"
    )

    draw.rounded_rectangle(
        (100, 410, 620, 500),
        radius=25,
        fill="#E62117",
        outline="white",
        width=3
    )

    centered_text(
        draw,
        "SUBSCRIBE",
        433,
        get_font(32, True),
        "white"
    )

    centered_text(
        draw,
        "LIKE  👍  BELL",
        525,
        get_font(25, True),
        "#FFE47A"
    )

    draw.rounded_rectangle(
        (25, 1040, WIDTH - 25, 1190),
        radius=25,
        fill="#13294B",
        outline="white",
        width=3
    )

    centered_text(
        draw,
        "नई कहानियों के लिए जुड़े रहें!",
        1080,
        get_font(24, True),
        "white"
    )

    image.save(path)


# ==========================================
# HINDI NARRATION
# ==========================================

async def create_voice(text, audio_path):
    speech = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%"
    )

    await asyncio.wait_for(
        speech.save(str(audio_path)),
        timeout=180
    )


def get_audio_duration(audio_path):
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

    return max(4.0, float(result.stdout.strip()) + 0.5)


# ==========================================
# CREATE A CLIP
# ==========================================

def create_clip(image_path, audio_path, video_path, duration):
    frames = max(1, int(duration * FPS))

    video_filter = (
        "scale=800:1422:force_original_aspect_ratio=increase,"
        "crop=800:1422,"
        f"zoompan=z='min(zoom+0.0004,1.05)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "format=yuv420p"
    )

    run_command([
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),
        "-i", str(audio_path),
        "-vf", video_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-t", f"{duration:.2f}",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(video_path)
    ])


# ==========================================
# COMBINE CLIPS AND MUSIC
# ==========================================

def combine_clips(videos, final_path):
    concat_file = final_path.parent / "concat.txt"

    with concat_file.open("w", encoding="utf-8") as file:
        for video in videos:
            file.write(
                f"file '{video.resolve().as_posix()}'\n"
            )

    if MUSIC_FILE.exists():
        print("Adding background music...", flush=True)

        run_command([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-stream_loop", "-1",
            "-i", str(MUSIC_FILE),
            "-filter_complex",
            "[1:a]volume=0.12[m];"
            "[0:a][m]amix=inputs=2:duration=first:"
            "dropout_transition=2[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(final_path)
        ])
    else:
        print("No background music; using narration only.")

        run_command([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-movflags", "+faststart",
            str(final_path)
        ])


# ==========================================
# CREATE LANDSCAPE VERSION
# ==========================================

def create_landscape(vertical_file, landscape_file):
    print("Creating landscape version...", flush=True)

    video_filter = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,boxblur=20:10[background];"
        "[fg]scale=607:1080:force_original_aspect_ratio=decrease,"
        "setsar=1[foreground];"
        "[background][foreground]overlay=(W-w)/2:(H-h)/2,"
        "format=yuv420p[v]"
    )

    run_command([
        "ffmpeg", "-y",
        "-i", str(vertical_file),
        "-filter_complex", video_filter,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(landscape_file)
    ])


# ==========================================
# MAIN
# ==========================================

def main():
    print("=" * 55)
    print("KYA BACHE - FREE HINDI STORY VIDEO")
    print("=" * 55, flush=True)

    check_tools()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_dir = OUTPUT_DIR / datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    clips = []

    for number, scene in enumerate(STORY, start=1):
        print(
            f"Creating scene {number}/{len(STORY)}...",
            flush=True
        )

        image_path = create_scene_image(
            scene, number, run_dir
        )

        audio_path = run_dir / f"voice_{number:02d}.mp3"
        video_path = run_dir / f"clip_{number:02d}.mp4"

        asyncio.run(
            create_voice(scene["text"], audio_path)
        )

        duration = get_audio_duration(audio_path)

        create_clip(
            image_path,
            audio_path,
            video_path,
            duration
        )

        clips.append(video_path)

    # Create subscribe outro.
    print("Creating subscribe outro...", flush=True)

    outro_image = run_dir / "subscribe_outro.png"
    outro_audio = run_dir / "subscribe_outro.mp3"
    outro_video = run_dir / "subscribe_outro.mp4"

    create_outro_image(outro_image)

    asyncio.run(
        create_voice(
            SUBSCRIBE_MESSAGE,
            outro_audio
        )
    )

    outro_duration = get_audio_duration(outro_audio)

    create_clip(
        outro_image,
        outro_audio,
        outro_video,
        outro_duration
    )

    clips.append(outro_video)

    # Create complete vertical video.
    vertical_file = OUTPUT_DIR / "daily_video.mp4"

    print("Combining complete vertical story...", flush=True)
    combine_clips(clips, vertical_file)

    # Create complete landscape video from the same full story.
    landscape_file = OUTPUT_DIR / "daily_video_landscape.mp4"

    create_landscape(
        vertical_file,
        landscape_file
    )

    print("=" * 55)
    print("VIDEO GENERATION SUCCESSFUL")
    print("Vertical video:", vertical_file)
    print("Landscape video:", landscape_file)
    print("Gemini API used: NO")
    print("=" * 55, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR:", error, flush=True)
        raise SystemExit(1)
