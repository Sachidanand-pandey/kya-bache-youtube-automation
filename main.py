
import os
import math
import asyncio
import random
import subprocess
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ==========================================
# KYA BACHE - FREE VIDEO AUTOMATION
# ==========================================

WIDTH = 720
HEIGHT = 1280
FPS = 25
VOICE = "hi-IN-SwaraNeural"

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "output"
MUSIC = BASE / "music" / "background.mp3"

# A different story and quiz are selected each run.
STORIES = [
    {
        "title": "चालाक खरगोश और जादुई पेड़",
        "scenes": [
            ("एक जंगल में चिंटू नाम का खरगोश रहता था।",
             "rabbit"),
            ("एक दिन उसे एक चमकता हुआ जादुई पेड़ मिला।",
             "tree"),
            ("पेड़ ने बताया कि जंगल का पानी सूख रहा है।",
             "water"),
            ("चिंटू ने बंद झरने का रास्ता खोजा।",
             "rabbit"),
            ("उसने बंद रास्ते से पत्ते और टहनियाँ हटाईं।",
             "water"),
            ("धीरे-धीरे झरने से साफ पानी बहने लगा।",
             "water"),
            ("सभी जानवर खुशी से नाचने लगे।",
             "happy"),
            ("चिंटू ने सीखा कि मिलकर काम करने से बड़ी समस्या हल होती है।",
             "happy")
        ],
        "moral": "सीख: मिल-जुलकर काम करना चाहिए।"
    },
    {
        "title": "नीली चिड़िया की मदद",
        "scenes": [
            ("मोहन एक सुंदर गाँव में रहता था।",
             "boy"),
            ("एक दिन उसे पेड़ के नीचे नीली चिड़िया मिली।",
             "bird"),
            ("चिड़िया उड़ नहीं पा रही थी।",
             "bird"),
            ("मोहन उसके लिए पानी लेकर आया।",
             "water"),
            ("एक सफेद खरगोश भी उसकी मदद करने आया।",
             "rabbit"),
            ("थोड़ी देर बाद चिड़िया ठीक महसूस करने लगी।",
             "happy"),
            ("चिड़िया ने अपने नीले पंख फैलाए और उड़ गई।",
             "bird"),
            ("मोहन ने सीखा कि हमें सभी जीवों की मदद करनी चाहिए।",
             "happy")
        ],
        "moral": "सीख: दया करना अच्छी आदत है।"
    },
    {
        "title": "ईमानदार बंदर",
        "scenes": [
            ("एक जंगल में गोलू बंदर रहता था।",
             "monkey"),
            ("उसे रास्ते में केले से भरी टोकरी मिली।",
             "banana"),
            ("गोलू को बहुत भूख लगी थी।",
             "monkey"),
            ("लेकिन उसने टोकरी अपने पास नहीं रखी।",
             "banana"),
            ("वह टोकरी के मालिक को खोजने निकला।",
             "monkey"),
            ("थोड़ी दूर उसे एक बूढ़ा हाथी मिला।",
             "elephant"),
            ("हाथी ने बताया कि टोकरी उसी की थी।",
             "banana"),
            ("गोलू को ईमानदारी के लिए सबने धन्यवाद दिया।",
             "happy")
        ],
        "moral": "सीख: हमेशा ईमानदार रहना चाहिए।"
    }
]

QUIZZES = [
    {
        "question": "बताओ, कौन सा पक्षी रात में जागता है?",
        "options": "कबूतर, उल्लू या तोता?",
        "answer": "सही जवाब है उल्लू!",
        "kind": "bird"
    },
    {
        "question": "किस जानवर की लंबी सूँड़ होती है?",
        "options": "हाथी, खरगोश या बिल्ली?",
        "answer": "सही जवाब है हाथी!",
        "kind": "elephant"
    },
    {
        "question": "कौन सा फल बंदर को बहुत पसंद है?",
        "options": "केला, प्याज या नींबू?",
        "answer": "सही जवाब है केला!",
        "kind": "banana"
    },
    {
        "question": "कौन सा जानवर जंगल का राजा कहलाता है?",
        "options": "शेर, खरगोश या चूहा?",
        "answer": "सही जवाब है शेर!",
        "kind": "lion"
    },
    {
        "question": "आसमान में रात को क्या चमकता है?",
        "options": "चाँद, जूता या कुर्सी?",
        "answer": "सही जवाब है चाँद और तारे!",
        "kind": "moon"
    }
]


def run_command(command, timeout=1200):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-3000:])


def font(size, bold=False):
    if os.name == "nt":
        names = [
            r"C:\Windows\Fonts\NirmalaB.ttf"
            if bold else r"C:\Windows\Fonts\Nirmala.ttf",
            r"C:\Windows\Fonts\arialbd.ttf"
            if bold else r"C:\Windows\Fonts\arial.ttf"
        ]
    else:
        names = [
            "/usr/share/fonts/truetype/noto/"
            + ("NotoSansDevanagari-Bold.ttf"
               if bold else "NotoSansDevanagari-Regular.ttf"),
            "/usr/share/fonts/truetype/dejavu/"
            + ("DejaVuSans-Bold.ttf"
               if bold else "DejaVuSans.ttf")
        ]

    for name in names:
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
    return ImageFont.load_default()


def centered(draw, text, y, fnt, color="white"):
    box = draw.textbbox((0, 0), text, font=fnt)
    x = (WIDTH - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=fnt, fill=color)


def background(draw):
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill="#91DFFF")
    draw.ellipse((530, 70, 640, 180), fill="#FFD94D")
    draw.ellipse((-150, 480, 420, 1000), fill="#6BC775")
    draw.ellipse((270, 470, 900, 1000), fill="#339C52")
    draw.rectangle((0, 820, WIDTH, HEIGHT), fill="#4CAF50")

    for x, y in [(45, 570), (590, 550)]:
        draw.rectangle((x + 35, y + 80, x + 60, y + 240),
                       fill="#80502B")
        draw.ellipse((x, y, x + 100, y + 135),
                     fill="#248646")


def boy(draw, x, y, s=1):
    draw.ellipse((x, y, x+90*s, y+90*s), fill="#F4BD87")
    draw.pieslice((x-4*s, y-12*s, x+94*s, y+60*s),
                  180, 360, fill="#51311F")
    for ex in (x+27*s, x+63*s):
        draw.ellipse((ex, y+36*s, ex+8*s, y+45*s),
                     fill="#222222")
    draw.arc((x+28*s, y+45*s, x+65*s, y+70*s),
             0, 180, fill="#9C3B35", width=3)
    draw.rounded_rectangle(
        (x-5*s, y+90*s, x+95*s, y+220*s),
        radius=15, fill="#F04C4C"
    )
    draw.line((x+20*s, y+215*s, x+12*s, y+285*s),
              fill="#244D9A", width=max(6, int(18*s)))
    draw.line((x+70*s, y+215*s, x+78*s, y+285*s),
              fill="#244D9A", width=max(6, int(18*s)))


def bird(draw, x, y, s=1):
    draw.ellipse((x, y, x+115*s, y+80*s), fill="#2188F5")
    draw.ellipse((x+20*s, y+15*s, x+80*s, y+70*s),
                 fill="#61BCFF")
    draw.ellipse((x+70*s, y-25*s, x+135*s, y+40*s),
                 fill="#2188F5")
    draw.ellipse((x+110*s, y-5*s, x+122*s, y+7*s),
                 fill="white")
    draw.ellipse((x+114*s, y-2*s, x+120*s, y+4*s),
                 fill="#222222")
    draw.polygon([
        (x+132*s, y+5*s),
        (x+158*s, y+14*s),
        (x+132*s, y+23*s)
    ], fill="#FFB52E")


def rabbit(draw, x, y, s=1):
    draw.ellipse((x+10*s, y-70*s, x+40*s, y+20*s),
                 fill="white")
    draw.ellipse((x+50*s, y-80*s, x+80*s, y+20*s),
                 fill="white")
    draw.ellipse((x, y+40*s, x+110*s, y+140*s),
                 fill="white")
    draw.ellipse((x+15*s, y, x+100*s, y+90*s),
                 fill="white")
    draw.ellipse((x+35*s, y+28*s, x+44*s, y+38*s),
                 fill="#222222")
    draw.ellipse((x+72*s, y+28*s, x+81*s, y+38*s),
                 fill="#222222")
    draw.ellipse((x+56*s, y+45*s, x+65*s, y+54*s),
                 fill="#F18AA2")


def draw_character(draw, kind):
    if kind in ("boy", "water"):
        boy(draw, 240, 620, 1)
    elif kind == "bird":
        boy(draw, 90, 650, 0.8)
        bird(draw, 420, 650, 1)
    elif kind == "rabbit":
        rabbit(draw, 300, 750, 1)
    elif kind == "tree":
        draw.rectangle((300, 530, 410, 900), fill="#80502B")
        draw.ellipse((190, 350, 520, 650), fill="#258B43")
        draw.ellipse((260, 300, 480, 510), fill="#41AF58")
        draw.ellipse((315, 430, 350, 465), fill="#FFE66B")
    elif kind == "monkey":
        draw.ellipse((230, 570, 450, 800), fill="#A96935")
        draw.ellipse((260, 510, 420, 680), fill="#A96935")
        draw.ellipse((290, 570, 315, 595), fill="white")
        draw.ellipse((360, 570, 385, 595), fill="white")
        draw.arc((300, 590, 375, 645), 0, 180, fill="#321E10", width=5)
    elif kind == "banana":
        draw.arc((250, 560, 490, 850), 10, 170,
                 fill="#FFDA36", width=45)
    elif kind == "elephant":
        draw.ellipse((200, 570, 500, 830), fill="#A6AEB9")
        draw.ellipse((240, 500, 460, 700), fill="#A6AEB9")
        draw.ellipse((200, 540, 300, 670), fill="#8795A6")
        draw.line((410, 620, 430, 700, 410, 740),
                  fill="#A6AEB9", width=45)
        draw.ellipse((365, 555, 380, 570), fill="#222222")
    elif kind == "lion":
        draw.ellipse((190, 500, 510, 830), fill="#C67A27")
        draw.ellipse((245, 550, 455, 760), fill="#E7B16A")
        draw.ellipse((290, 610, 310, 630), fill="#222222")
        draw.ellipse((390, 610, 410, 630), fill="#222222")
        draw.arc((320, 635, 385, 685), 0, 180, fill="#6E3515", width=4)
    elif kind == "moon":
        draw.ellipse((245, 450, 480, 685), fill="#FFF0A6")
        draw.ellipse((315, 410, 510, 640), fill="#91DFFF")
        for x, y in [(200, 420), (500, 480), (240, 720), (470, 760)]:
            draw.ellipse((x, y, x+15, y+15), fill="white")
    elif kind == "happy":
        boy(draw, 70, 650, 0.8)
        bird(draw, 420, 620, 0.9)
        rabbit(draw, 500, 800, 0.65)
    else:
        bird(draw, 300, 600, 1)


def wrap_lines(draw, text, fnt, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + " " + word if current else word
        box = draw.textbbox((0, 0), test, font=fnt)
        if box[2] - box[0] > max_width:
            if current:
                lines.append(current)
            current = word
        else:
            current = test

    if current:
        lines.append(current)
    return lines


def create_scene_image(text, kind, number, folder, label):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    background(draw)
    draw_character(draw, kind)

    draw.rounded_rectangle((20, 25, WIDTH-20, 150),
                           radius=22, fill="#173A6C",
                           outline="white", width=3)
    centered(draw, label, 48, font(30, True))
    centered(draw, f"दृश्य {number}", 95, font(22),
             "#FFE47A")

    draw.rounded_rectangle((25, 980, WIDTH-25, 1220),
                           radius=22, fill="#173A6C",
                           outline="white", width=3)

    fnt = font(25)
    lines = wrap_lines(draw, text, fnt, WIDTH-80)
    y = 1010
    for line in lines[:5]:
        centered(draw, line, y, fnt)
        y += 39

    path = folder / f"scene_{number:02d}.png"
    image.save(path)
    return path


def create_outro(folder):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#173A6C")
    draw = ImageDraw.Draw(image)
    background(draw)
    draw_character(draw, "happy")

    draw.rounded_rectangle((25, 300, WIDTH-25, 590),
                           radius=30, fill="#13294B",
                           outline="white", width=4)
    centered(draw, "कहानी अच्छी लगी?", 330, font(38, True))
    draw.rounded_rectangle((100, 410, 620, 500),
                           radius=25, fill="#E62117",
                           outline="white", width=3)
    centered(draw, "SUBSCRIBE", 433, font(32, True))
    centered(draw, "LIKE  👍  BELL", 525, font(25, True),
             "#FFE47A")
    centered(draw, "नई कहानियों के लिए जुड़े रहें!",
             1100, font(24, True))
    path = folder / "subscribe.png"
    image.save(path)
    return path


async def create_voice(text, path):
    tts = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%"
    )
    await asyncio.wait_for(tts.save(str(path)), timeout=180)


def duration_of(path):
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ], capture_output=True, text=True, timeout=30)

    return max(4.0, float(result.stdout.strip()) + 0.5)


def make_clip(image, audio, video, duration):
    frames = max(1, int(duration * FPS))
    run_command([
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image),
        "-i", str(audio),
        "-vf",
        "scale=800:1422:force_original_aspect_ratio=increase,"
        "crop=800:1422,"
        f"zoompan=z='min(zoom+0.0004,1.05)':d={frames}:"
        f"s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-t", f"{duration:.2f}",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(video)
    ])


def combine(clips, destination):
    concat = destination.parent / (destination.stem + "_concat.txt")
    with concat.open("w", encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    if MUSIC.exists():
        run_command([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat),
            "-stream_loop", "-1",
            "-i", str(MUSIC),
            "-filter_complex",
            "[1:a]volume=0.12[m];"
            "[0:a][m]amix=inputs=2:duration=first:"
            "dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(destination)
        ])
    else:
        run_command([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat),
            "-c", "copy",
            "-movflags", "+faststart",
            str(destination)
        ])


def landscape(source, destination):
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
        "ffmpeg", "-y", "-i", str(source),
        "-filter_complex", video_filter,
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-crf", "23", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(destination)
    ])


def build_video(text_scenes, folder, prefix, label, outro=True):
    clips = []

    for number, (text, kind) in enumerate(text_scenes, start=1):
        print(f"{prefix}: scene {number}/{len(text_scenes)}",
              flush=True)
        img = create_scene_image(
            text, kind, number, folder, label
        )
        audio = folder / f"{prefix}_voice_{number:02d}.mp3"
        clip = folder / f"{prefix}_clip_{number:02d}.mp4"

        asyncio.run(create_voice(text, audio))
        make_clip(img, audio, clip, duration_of(audio))
        clips.append(clip)

    if outro:
        img = create_outro(folder)
        audio = folder / f"{prefix}_outro.mp3"
        clip = folder / f"{prefix}_outro.mp4"
        asyncio.run(create_voice(SUBSCRIBE_MESSAGE, audio))
        make_clip(img, audio, clip, duration_of(audio))
        clips.append(clip)

    result = folder / f"{prefix}_vertical.mp4"
    combine(clips, result)
    return result


SUBSCRIBE_MESSAGE = (
    "ऐसी और मज़ेदार कहानियों के लिए हमारे चैनल को सब्सक्राइब करें। "
    "वीडियो अच्छी लगी हो तो लाइक करें।"
)


def main():
    for tool in ("ffmpeg", "ffprobe"):
        check = subprocess.run([tool, "-version"], capture_output=True)
        if check.returncode != 0:
            raise RuntimeError(f"{tool} not installed.")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    folder = OUTPUT / datetime.now().strftime("%Y%m%d_%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)

    story = random.choice(STORIES)
    quiz = random.choice(QUIZZES)

    print("Selected story:", story["title"], flush=True)

    # Full story for the regular video.
    story_scenes = list(story["scenes"])
    story_scenes[-1] = (
        story_scenes[-1][0] + " " + story["moral"],
        story_scenes[-1][1]
    )

    story_vertical = build_video(
        story_scenes, folder, "story",
        story["title"], outro=True
    )

    # Convert the complete story to landscape.
    landscape(
        story_vertical,
        OUTPUT / "daily_video.mp4"
    )

    # A separate riddle/quiz Short, not a shortened story.
    quiz_scenes = [
        (quiz["question"], quiz["kind"]),
        (quiz["options"], quiz["kind"]),
        ("सोचने के लिए तीन सेकंड हैं!", quiz["kind"]),
        (quiz["answer"], quiz["kind"])
    ]

    quiz_vertical = build_video(
        quiz_scenes, folder, "short",
        "आज का मज़ेदार सवाल", outro=True
    )

    # Store the Short under a stable filename for uploading.
    run_command([
        "ffmpeg", "-y", "-i", str(quiz_vertical),
        "-c", "copy",
        str(OUTPUT / "daily_short.mp4")
    ])

    print("SUCCESS")
    print("Full landscape story:", OUTPUT / "daily_video.mp4")
    print("Separate quiz Short:", OUTPUT / "daily_short.mp4")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR:", error, flush=True)
        raise SystemExit(1)
