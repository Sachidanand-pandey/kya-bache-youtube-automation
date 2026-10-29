
import os
import math
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ==========================================
# KYA BACHE - FREE HINDI STORY VIDEO
# No Gemini API required
# ==========================================

WIDTH = 720
HEIGHT = 1280
FPS = 25
VOICE = "hi-IN-SwaraNeural"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
MUSIC_FILE = BASE_DIR / "music" / "background.mp3"

# Use a timestamped folder for each generation.
RUN_DIR = OUTPUT_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")


# ==========================================
# STORY
# ==========================================

def create_story():
    return {
        "title": "नीली चिड़िया और प्यारा बच्चा",
        "scenes": [
            {
                "text": "एक सुंदर जंगल में मोहन नाम का एक प्यारा बच्चा रहता था। "
                        "उसे जानवरों और पक्षियों से बहुत प्यार था।",
                "kind": "forest"
            },
            {
                "text": "एक दिन मोहन को पेड़ के नीचे एक छोटी नीली चिड़िया मिली। "
                        "चिड़िया उदास थी और उड़ नहीं पा रही थी।",
                "kind": "bird"
            },
            {
                "text": "मोहन ने प्यार से चिड़िया को अपने हाथों में उठाया। "
                        "उसने चिड़िया को थोड़ा पानी पिलाया।",
                "kind": "water"
            },
            {
                "text": "पास ही एक सफेद खरगोश भी आ गया। "
                        "दोनों ने मिलकर चिड़िया की मदद की।",
                "kind": "rabbit"
            },
            {
                "text": "कुछ देर बाद नीली चिड़िया खुश हो गई। "
                        "उसने अपने सुंदर पंख फैलाए।",
                "kind": "happy"
            },
            {
                "text": "चिड़िया ने धीरे-धीरे उड़ना शुरू किया। "
                        "मोहन और खरगोश उसे देखकर बहुत खुश हुए।",
                "kind": "fly"
            },
            {
                "text": "नीली चिड़िया आसमान में उड़कर वापस आई। "
                        "वह मोहन के लिए एक सुंदर फूल लेकर आई।",
                "kind": "flower"
            },
            {
                "text": "मोहन ने सीखा कि दूसरों की मदद करना बहुत अच्छी बात है। "
                        "हमें हमेशा जानवरों और पक्षियों से प्यार करना चाहिए।",
                "kind": "ending"
            }
        ],
        "moral": "दूसरों की मदद करना सबसे अच्छी आदत है।"
    }


# ==========================================
# FONT
# ==========================================

def get_font(size, bold=False):
    if os.name == "nt":
        candidates = [
            r"C:\Windows\Fonts\NirmalaB.ttf"
            if bold else r"C:\Windows\Fonts\Nirmala.ttf",
            r"C:\Windows\Fonts\arialbd.ttf"
            if bold else r"C:\Windows\Fonts\arial.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/noto/"
            + ("NotoSansDevanagari-Bold.ttf"
               if bold else "NotoSansDevanagari-Regular.ttf"),
            "/usr/share/fonts/truetype/dejavu/"
            + ("DejaVuSans-Bold.ttf"
               if bold else "DejaVuSans.ttf")
        ]

    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass

    return ImageFont.load_default()


# ==========================================
# DRAWING HELPERS
# ==========================================

def draw_centered(draw, text, y, font, fill, width=WIDTH):
    box = draw.textbbox((0, 0), text, font=font)
    text_width = box[2] - box[0]
    x = (width - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)


def draw_background(draw):
    # Sky
    draw.rectangle((0, 0, WIDTH, 800), fill="#8ED6FF")

    # Sun
    draw.ellipse((535, 90, 650, 205), fill="#FFD75E")

    # Clouds
    for x, y in [(80, 130), (320, 210), (500, 300)]:
        draw.ellipse((x, y, x + 90, y + 45), fill="white")
        draw.ellipse((x + 25, y - 20, x + 75, y + 40), fill="white")
        draw.ellipse((x + 55, y, x + 115, y + 45), fill="white")

    # Hills
    draw.ellipse((-180, 510, 450, 1050), fill="#6CCB77")
    draw.ellipse((230, 470, 900, 1050), fill="#38A95B")

    # Grass
    draw.rectangle((0, 820, WIDTH, HEIGHT), fill="#4DAE57")

    # Trees
    for x, y in [(55, 580), (600, 550)]:
        draw.rectangle((x + 35, y + 100, x + 65, y + 250),
                       fill="#87502D")
        draw.ellipse((x, y, x + 100, y + 150),
                     fill="#218B49")
        draw.ellipse((x + 15, y - 35, x + 105, y + 90),
                     fill="#2E9F50")


def draw_boy(draw, x, y, scale=1.0):
    # x,y is top of head.
    s = scale

    # Hair and face
    draw.ellipse((x, y, x + 100*s, y + 100*s),
                 fill="#F4BE88")
    draw.pieslice((x - 5*s, y - 10*s, x + 105*s, y + 70*s),
                  180, 360, fill="#51301F")

    # Eyes
    draw.ellipse((x + 25*s, y + 40*s, x + 35*s, y + 52*s),
                 fill="#222222")
    draw.ellipse((x + 65*s, y + 40*s, x + 75*s, y + 52*s),
                 fill="#222222")

    # Smile
    draw.arc((x + 35*s, y + 52*s, x + 68*s, y + 78*s),
             0, 180, fill="#9E3B35", width=max(2, int(3*s)))

    # Shirt and body
    draw.rounded_rectangle(
        (x - 10*s, y + 95*s, x + 110*s, y + 245*s),
        radius=int(20*s),
        fill="#F04B4B"
    )

    # Arms
    draw.line(
        (x, y + 120*s, x - 45*s, y + 180*s),
        fill="#F4BE88",
        width=max(8, int(18*s))
    )
    draw.line(
        (x + 100*s, y + 120*s, x + 145*s, y + 180*s),
        fill="#F4BE88",
        width=max(8, int(18*s))
    )

    # Legs
    draw.line(
        (x + 25*s, y + 235*s, x + 15*s, y + 310*s),
        fill="#244C9A",
        width=max(8, int(22*s))
    )
    draw.line(
        (x + 75*s, y + 235*s, x + 85*s, y + 310*s),
        fill="#244C9A",
        width=max(8, int(22*s))
    )

    # Shoes
    draw.ellipse((x - 5*s, y + 295*s, x + 30*s, y + 320*s),
                 fill="#51301F")
    draw.ellipse((x + 70*s, y + 295*s, x + 110*s, y + 320*s),
                 fill="#51301F")


def draw_bird(draw, x, y, scale=1.0):
    s = scale

    # Body
    draw.ellipse((x, y, x + 125*s, y + 90*s),
                 fill="#2388F5")

    # Wing
    draw.ellipse((x + 20*s, y + 15*s, x + 85*s, y + 75*s),
                 fill="#57B5FF")

    # Head
    draw.ellipse((x + 75*s, y - 30*s, x + 145*s, y + 40*s),
                 fill="#2388F5")

    # Eye
    draw.ellipse((x + 118*s, y - 5*s, x + 130*s, y + 7*s),
                 fill="white")
    draw.ellipse((x + 122*s, y - 2*s, x + 128*s, y + 4*s),
                 fill="#111111")

    # Beak
    draw.polygon([
        (x + 140*s, y + 5*s),
        (x + 165*s, y + 15*s),
        (x + 140*s, y + 22*s)
    ], fill="#FFB52E")

    # Tail
    draw.polygon([
        (x + 5*s, y + 30*s),
        (x - 30*s, y + 5*s),
        (x - 20*s, y + 48*s)
    ], fill="#1663C7")

    # Feet
    draw.line((x + 45*s, y + 82*s, x + 42*s, y + 102*s),
              fill="#FFB52E", width=max(2, int(4*s)))
    draw.line((x + 75*s, y + 82*s, x + 72*s, y + 102*s),
              fill="#FFB52E", width=max(2, int(4*s)))


def draw_rabbit(draw, x, y, scale=1.0):
    s = scale

    # Ears
    draw.ellipse((x + 10*s, y - 80*s, x + 40*s, y + 20*s),
                 fill="white")
    draw.ellipse((x + 50*s, y - 90*s, x + 80*s, y + 20*s),
                 fill="white")

    # Body and head
    draw.ellipse((x, y + 50*s, x + 110*s, y + 145*s),
                 fill="white")
    draw.ellipse((x + 20*s, y, x + 105*s, y + 90*s),
                 fill="white")

    # Eyes and nose
    draw.ellipse((x + 40*s, y + 28*s, x + 49*s, y + 38*s),
                 fill="#222222")
    draw.ellipse((x + 75*s, y + 28*s, x + 84*s, y + 38*s),
                 fill="#222222")
    draw.ellipse((x + 59*s, y + 44*s, x + 68*s, y + 53*s),
                 fill="#F18AA2")


# ==========================================
# CREATE A SCENE ILLUSTRATION
# ==========================================

def make_scene_image(scene, number, folder):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    draw_background(draw)

    kind = scene["kind"]

    if kind == "forest":
        draw_boy(draw, 255, 620, 1.15)
        draw_bird(draw, 480, 630, 0.85)

    elif kind == "bird":
        draw_boy(draw, 120, 650, 0.95)
        draw_bird(draw, 445, 700, 1.0)

    elif kind == "water":
        draw_boy(draw, 140, 650, 0.95)
        draw_bird(draw, 425, 735, 0.8)
        draw.ellipse((395, 840, 515, 880), fill="#71D8FF")
        draw.ellipse((420, 850, 440, 858), fill="#FFFFFF")

    elif kind == "rabbit":
        draw_boy(draw, 75, 650, 0.9)
        draw_bird(draw, 325, 720, 0.75)
        draw_rabbit(draw, 500, 760, 0.85)

    elif kind == "happy":
        draw_boy(draw, 110, 640, 0.95)
        draw_bird(draw, 430, 620, 1.0)
        draw_rabbit(draw, 510, 790, 0.65)

    elif kind == "fly":
        draw_boy(draw, 110, 670, 0.95)
        draw_bird(draw, 460, 380, 0.9)
        draw_rabbit(draw, 510, 800, 0.65)

    elif kind == "flower":
        draw_boy(draw, 115, 650, 0.95)
        draw_bird(draw, 430, 630, 0.9)

        # Flower
        fx, fy = 540, 880
        draw.line((fx, fy, fx, fy + 65), fill="#24863D", width=7)
        for angle in range(0, 360, 60):
            a = math.radians(angle)
            cx = fx + int(15 * math.cos(a))
            cy = fy + int(15 * math.sin(a))
            draw.ellipse((cx - 10, cy - 10, cx + 10, cy + 10),
                         fill="#FF77B7")
        draw.ellipse((fx - 8, fy - 8, fx + 8, fy + 8),
                     fill="#FFD447")

    else:
        draw_boy(draw, 110, 650, 0.95)
        draw_bird(draw, 430, 620, 0.9)
        draw_rabbit(draw, 510, 800, 0.65)

    # Story title card
    draw.rounded_rectangle(
        (35, 35, WIDTH - 35, 170),
        radius=25,
        fill="#173A6C",
        outline="#FFFFFF",
        width=3
    )

    title_font = get_font(34, bold=True)
    small_font = get_font(23)

    draw_centered(
        draw,
        "कहानी का मज़ेदार सफर",
        55,
        title_font,
        "white"
    )

    draw_centered(
        draw,
        f"दृश्य {number}",
        112,
        small_font,
        "#FFE47A"
    )

    # Caption area
    draw.rounded_rectangle(
        (30, 1010, WIDTH - 30, 1210),
        radius=25,
        fill="#173A6C",
        outline="white",
        width=3
    )

    caption_font = get_font(25)
    words = scene["text"].split()
    lines = []
    current = ""

    for word in words:
        test = current + " " + word if current else word
        box = draw.textbbox((0, 0), test, font=caption_font)

        if box[2] - box[0] > WIDTH - 95:
            if current:
                lines.append(current)
            current = word
        else:
            current = test

    if current:
        lines.append(current)

    y = 1035
    for line in lines[:4]:
        draw_centered(draw, line, y, caption_font, "white")
        y += 40

    path = folder / f"scene_{number:02d}.png"
    image.save(path)

    return path


# ==========================================
# CREATE HINDI VOICE
# ==========================================

async def create_voice(text, output_path):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%"
    )

    await asyncio.wait_for(
        communicate.save(str(output_path)),
        timeout=180
    )


def audio_duration(audio_path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    try:
        return max(4.0, float(result.stdout.strip()) + 0.5)
    except (ValueError, AttributeError):
        return 6.0


# ==========================================
# FFMPEG HELPERS
# ==========================================

def run_command(command, timeout=900):
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


def make_scene_video(image_path, audio_path, video_path, duration):
    frames = int(duration * FPS)

    run_command([
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),
        "-i", str(audio_path),
        "-vf",
        "scale=800:1422:force_original_aspect_ratio=increase,"
        "crop=800:1422,"
        f"zoompan=z='min(zoom+0.0004,1.06)':d={frames}:"
        f"s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-t", str(duration),
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(video_path)
    ], timeout=900)


# ==========================================
# SUBSCRIBE OUTRO
# ==========================================

def make_outro_image(path):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#132F58")
    draw = ImageDraw.Draw(image)

    draw_background(draw)

    draw_boy(draw, 70, 660, 0.8)
    draw_bird(draw, 450, 640, 0.9)
    draw_rabbit(draw, 490, 850, 0.65)

    draw.rounded_rectangle(
        (35, 300, WIDTH - 35, 580),
        radius=35,
        fill="#12294B",
        outline="white",
        width=4
    )

    title_font = get_font(39, bold=True)
    button_font = get_font(32, bold=True)
    small_font = get_font(25)

    draw_centered(
        draw, "कहानी अच्छी लगी?",
        330, title_font, "white"
    )

    draw.rounded_rectangle(
        (105, 410, 615, 500),
        radius=25,
        fill="#E62117",
        outline="white",
        width=3
    )

    draw_centered(
        draw, "SUBSCRIBE",
        433, button_font, "white"
    )

    draw_centered(
        draw, "👍 LIKE     🔔 BELL",
        520, small_font, "#FFE47A"
    )

    draw.rounded_rectangle(
        (35, 1040, WIDTH - 35, 1195),
        radius=25,
        fill="#12294B",
        outline="white",
        width=3
    )

    draw_centered(
        draw,
        "नई कहानियों के लिए जुड़े रहें!",
        1085,
        small_font,
        "white"
    )

    image.save(path)


# ==========================================
# COMBINE VIDEOS
# ==========================================

def combine_videos(videos, final_path):
    concat_path = final_path.parent / "concat.txt"

    with concat_path.open("w", encoding="utf-8") as file:
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
            "-i", str(concat_path),
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
        ], timeout=1800)

    else:
        run_command([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_path),
            "-c", "copy",
            "-movflags", "+faststart",
            str(final_path)
        ], timeout=1800)


# ==========================================
# MAIN
# ==========================================

def main():
    print("=" * 50)
    print("KYA BACHE - FREE HINDI STORY VIDEO")
    print("=" * 50)

    for tool in ("ffmpeg", "ffprobe"):
        check = subprocess.run(
            [tool, "-version"],
            capture_output=True
        )
        if check.returncode != 0:
            raise RuntimeError(
                f"{tool} is not installed or not in PATH."
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    story = create_story()
    videos = []

    # Generate eight illustrated scenes.
    for number, scene in enumerate(story["scenes"], start=1):
        print(
            f"Creating scene {number}/{len(story['scenes'])}...",
            flush=True
        )

        image_path = make_scene_image(
            scene, number, RUN_DIR
        )

        audio_path = RUN_DIR / f"voice_{number:02d}.mp3"
        video_path = RUN_DIR / f"video_{number:02d}.mp4"

        asyncio.run(
            create_voice(scene["text"], audio_path)
        )

        duration = audio_duration(audio_path)

        make_scene_video(
            image_path,
            audio_path,
            video_path,
            duration
        )

        videos.append(video_path)

    # Create the visible subscribe outro.
    print("Creating subscribe outro...", flush=True)

    outro_image = RUN_DIR / "subscribe_outro.png"
    outro_audio = RUN_DIR / "subscribe_outro.mp3"
    outro_video = RUN_DIR / "subscribe_outro.mp4"

    make_outro_image(outro_image)

    asyncio.run(
        create_voice(
            "ऐसी और मज़ेदार कहानियों के लिए "
            "हमारे चैनल को सब्सक्राइब करें। "
            "वीडियो अच्छी लगी हो तो लाइक करें। धन्यवाद!",
            outro_audio
        )
    )

    duration = audio_duration(outro_audio)

    make_scene_video(
        outro_image,
        outro_audio,
        outro_video,
        duration
    )

    videos.append(outro_video)

    # Produce a video in the run folder.
    timestamp_video = RUN_DIR / "daily_video.mp4"

    combine_videos(videos, timestamp_video)

    # Copy to the stable location expected by the uploader.
    stable_video = OUTPUT_DIR / "daily_video.mp4"

    run_command([
        "ffmpeg", "-y",
        "-i", str(timestamp_video),
        "-c", "copy",
        str(stable_video)
    ], timeout=900)

    print("=" * 50)
    print("VIDEO CREATED SUCCESSFULLY")
    print("Video:", stable_video)
    print("Run folder:", RUN_DIR)
    print("Gemini API used: NO")
    print("Local cartoon illustrations: YES")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR:", error, flush=True)
        raise SystemExit(1)
