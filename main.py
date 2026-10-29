
import os
import asyncio
import random
import subprocess
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import edge_tts

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "output"
MUSIC = BASE / "music" / "background.mp3"

VOICE = "hi-IN-SwaraNeural"
FPS = 25

LANDSCAPE = (1280, 720)
PORTRAIT = (720, 1280)

STORIES = [
    {
        "title": "चालाक खरगोश और जादुई पेड़",
        "scenes": [
            ("एक हरे-भरे जंगल में चिंटू नाम का खरगोश रहता था।", "rabbit"),
            ("एक सुबह उसे एक चमकता हुआ जादुई पेड़ दिखाई दिया।", "tree"),
            ("पेड़ ने बताया कि जंगल का झरना बंद हो गया है।", "tree"),
            ("चिंटू ने देखा कि झरने का रास्ता पत्थरों से बंद था।", "rabbit"),
            ("उसने अपने दोस्तों को बुलाया और सबने मिलकर मेहनत की।", "happy"),
            ("सभी ने मिलकर पत्थर और टहनियाँ हटा दीं।", "water"),
            ("साफ पानी फिर से बहने लगा और सभी जानवर खुश हो गए।", "happy"),
            ("चिंटू को समझ आया कि मिलकर काम करने से बड़ी समस्या हल होती है।", "rabbit"),
        ],
        "moral": "सीख: मिल-जुलकर काम करने से मुश्किल आसान हो जाती है।"
    },
    {
        "title": "नीली चिड़िया की मदद",
        "scenes": [
            ("एक गाँव में मोहन नाम का दयालु बच्चा रहता था।", "boy"),
            ("एक दिन उसे पेड़ के नीचे एक नीली चिड़िया मिली।", "bird"),
            ("चिड़िया थकी हुई थी और उड़ नहीं पा रही थी।", "bird"),
            ("मोहन उसके लिए पानी लेकर आया।", "boy"),
            ("उसने चिड़िया को सुरक्षित जगह पर आराम करने दिया।", "happy"),
            ("कुछ देर बाद चिड़िया फिर से चहकने लगी।", "bird"),
            ("चिड़िया ने अपने पंख फैलाए और आसमान में उड़ गई।", "bird"),
            ("मोहन खुश था कि उसकी मदद से एक जीव को राहत मिली।", "happy"),
        ],
        "moral": "सीख: हमें सभी जीवों के प्रति दयालु होना चाहिए।"
    },
    {
        "title": "ईमानदार बंदर",
        "scenes": [
            ("एक जंगल में गोलू नाम का बंदर रहता था।", "monkey"),
            ("एक दिन उसे केले से भरी टोकरी मिली।", "banana"),
            ("गोलू को भूख लगी थी, लेकिन उसने टोकरी नहीं रखी।", "monkey"),
            ("वह टोकरी के मालिक को खोजने निकल पड़ा।", "monkey"),
            ("रास्ते में उसे एक बूढ़ा हाथी परेशान दिखाई दिया।", "elephant"),
            ("हाथी ने बताया कि टोकरी उसी की थी।", "elephant"),
            ("गोलू ने टोकरी लौटा दी और हाथी बहुत खुश हुआ।", "happy"),
            ("जंगल के सभी जानवरों ने गोलू की तारीफ की।", "happy"),
        ],
        "moral": "सीख: हमेशा ईमानदार रहना चाहिए।"
    }
]

QUIZZES = [
    {
        "question": "कौन-सा पक्षी रात में जागता है?",
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
        "question": "बंदर को कौन-सा फल पसंद है?",
        "options": "केला, प्याज या नींबू?",
        "answer": "सही जवाब है केला!",
        "kind": "banana"
    },
    {
        "question": "जंगल का राजा किसे कहते हैं?",
        "options": "शेर, खरगोश या चूहा?",
        "answer": "सही जवाब है शेर!",
        "kind": "lion"
    },
    {
        "question": "रात में आसमान में क्या चमकता है?",
        "options": "चाँद-तारे, जूता या कुर्सी?",
        "answer": "सही जवाब है चाँद और तारे!",
        "kind": "moon"
    }
]


def run_command(command, timeout=1200):
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:] or "Command failed")


def get_font(size, bold=False):
    if os.name == "nt":
        fonts = [
            r"C:\Windows\Fonts\NirmalaB.ttf" if bold
            else r"C:\Windows\Fonts\Nirmala.ttf",
            r"C:\Windows\Fonts\arialbd.ttf" if bold
            else r"C:\Windows\Fonts\arial.ttf"
        ]
    else:
        fonts = [
            "/usr/share/fonts/truetype/noto/"
            + ("NotoSansDevanagari-Bold.ttf" if bold
               else "NotoSansDevanagari-Regular.ttf"),
            "/usr/share/fonts/truetype/dejavu/"
            + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
        ]

    for name in fonts:
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass

    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + " " + word if current else word
        width = draw.textbbox((0, 0), test, font=font)[2]

        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def centered(draw, text, y, font, width, color="white"):
    box = draw.textbbox((0, 0), text, font=font)
    x = (width - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=color)


def draw_character(draw, kind, width, height):
    cx = width // 2
    cy = int(height * 0.52)
    unit = min(width, height) / 700

    def ellipse(x1, y1, x2, y2, color):
        draw.ellipse(
            (int(x1), int(y1), int(x2), int(y2)),
            fill=color
        )

    if kind == "tree":
        draw.rectangle(
            (cx-25*unit, cy-10*unit, cx+25*unit, cy+190*unit),
            fill="#80502B"
        )
        ellipse(cx-150*unit, cy-190*unit,
                cx+150*unit, cy+70*unit, "#258B43")
        ellipse(cx-100*unit, cy-240*unit,
                cx+100*unit, cy-40*unit, "#41AF58")
        ellipse(cx-20*unit, cy-140*unit,
                cx+10*unit, cy-110*unit, "#FFE66B")

    elif kind in ("rabbit", "happy"):
        ellipse(cx-65*unit, cy-145*unit,
                cx-25*unit, cy-35*unit, "white")
        ellipse(cx+25*unit, cy-145*unit,
                cx+65*unit, cy-35*unit, "white")
        ellipse(cx-85*unit, cy-75*unit,
                cx+85*unit, cy+95*unit, "white")
        ellipse(cx-55*unit, cy-45*unit,
                cx+55*unit, cy+45*unit, "white")
        ellipse(cx-30*unit, cy-15*unit,
                cx-17*unit, cy-2*unit, "#222222")
        ellipse(cx+17*unit, cy-15*unit,
                cx+30*unit, cy-2*unit, "#222222")
        ellipse(cx-7*unit, cy+8*unit,
                cx+7*unit, cy+20*unit, "#F18AA2")

    elif kind in ("boy", "water"):
        ellipse(cx-65*unit, cy-125*unit,
                cx+65*unit, cy+5*unit, "#F4BD87")
        draw.pieslice(
            (cx-70*unit, cy-145*unit,
             cx+70*unit, cy-20*unit),
            180, 360, fill="#51311F"
        )
        ellipse(cx-35*unit, cy-75*unit,
                cx-22*unit, cy-62*unit, "#222222")
        ellipse(cx+22*unit, cy-75*unit,
                cx+35*unit, cy-62*unit, "#222222")
        draw.rounded_rectangle(
            (cx-70*unit, cy+5*unit,
             cx+70*unit, cy+170*unit),
            radius=max(1, int(15*unit)), fill="#F04C4C"
        )

    elif kind == "bird":
        ellipse(cx-105*unit, cy-40*unit,
                cx+45*unit, cy+60*unit, "#2188F5")
        ellipse(cx+5*unit, cy-105*unit,
                cx+95*unit, cy-15*unit, "#2188F5")
        ellipse(cx+40*unit, cy-75*unit,
                cx+57*unit, cy-58*unit, "white")
        ellipse(cx+46*unit, cy-70*unit,
                cx+54*unit, cy-62*unit, "#222222")
        draw.polygon(
            [(cx+85*unit, cy-65*unit),
             (cx+125*unit, cy-50*unit),
             (cx+85*unit, cy-35*unit)],
            fill="#FFB52E"
        )

    elif kind == "monkey":
        ellipse(cx-100*unit, cy-90*unit,
                cx+100*unit, cy+110*unit, "#A96935")
        ellipse(cx-75*unit, cy-150*unit,
                cx+75*unit, cy+5*unit, "#A96935")
        ellipse(cx-45*unit, cy-95*unit,
                cx-28*unit, cy-78*unit, "white")
        ellipse(cx+28*unit, cy-95*unit,
                cx+45*unit, cy-78*unit, "white")

    elif kind == "elephant":
        ellipse(cx-150*unit, cy-75*unit,
                cx+125*unit, cy+105*unit, "#A6AEB9")
        ellipse(cx-100*unit, cy-145*unit,
                cx+100*unit, cy+35*unit, "#A6AEB9")
        ellipse(cx-145*unit, cy-125*unit,
                cx-45*unit, cy-15*unit, "#8795A6")
        draw.line(
            (cx+65*unit, cy-35*unit,
             cx+90*unit, cy+45*unit,
             cx+65*unit, cy+75*unit),
            fill="#A6AEB9", width=max(10, int(35*unit))
        )

    elif kind == "banana":
        draw.arc(
            (cx-130*unit, cy-130*unit,
             cx+130*unit, cy+150*unit),
            10, 170, fill="#FFDA36",
            width=max(12, int(35*unit))
        )

    elif kind == "lion":
        ellipse(cx-150*unit, cy-150*unit,
                cx+150*unit, cy+150*unit, "#C67A27")
        ellipse(cx-100*unit, cy-100*unit,
                cx+100*unit, cy+100*unit, "#E7B16A")
        ellipse(cx-45*unit, cy-35*unit,
                cx-25*unit, cy-15*unit, "#222222")
        ellipse(cx+25*unit, cy-35*unit,
                cx+45*unit, cy-15*unit, "#222222")

    elif kind == "moon":
        ellipse(cx-110*unit, cy-110*unit,
                cx+110*unit, cy+110*unit, "#FFF0A6")
        ellipse(cx-30*unit, cy-145*unit,
                cx+150*unit, cy+55*unit, "#91DFFF")
        for dx, dy in [(-150, -120), (145, -75), (-110, 140)]:
            ellipse(cx+dx*unit, cy+dy*unit,
                    cx+(dx+15)*unit, cy+(dy+15)*unit, "white")

def make_scene(text, kind, number, label, size, folder):
    width, height = size
    image = Image.new("RGB", size, "#91DFFF")
    draw = ImageDraw.Draw(image)

    # Colorful landscape or portrait background.
    draw.ellipse(
        (width*.78, height*.05, width*.92, height*.22),
        fill="#FFD94D"
    )
    draw.ellipse(
        (-width*.18, height*.38, width*.48, height*.82),
        fill="#6BC775"
    )
    draw.ellipse(
        (width*.35, height*.36, width*1.15, height*.82),
        fill="#339C52"
    )
    draw.rectangle(
        (0, height*.68, width, height),
        fill="#4CAF50"
    )

    draw_character(draw, kind, width, height)

    margin = int(width*.035)
    header_height = int(height*.15)

    draw.rounded_rectangle(
        (margin, margin, width-margin, margin+header_height),
        radius=20, fill="#173A6C", outline="white", width=3
    )

    centered(
        draw, label, margin+int(header_height*.15),
        get_font(int(width*.035), True), width
    )
    centered(
        draw, f"दृश्य {number}", margin+int(header_height*.60),
        get_font(int(width*.025)), width, "#FFE47A"
    )

    box_height = int(height*.27)
    bottom = height-int(height*.035)
    top = bottom-box_height

    draw.rounded_rectangle(
        (margin, top, width-margin, bottom),
        radius=22, fill="#173A6C", outline="white", width=3
    )

    text_font = get_font(int(width*.032))
    lines = wrap_text(draw, text, text_font, width-margin*4)
    line_height = int(width*.044)
    y = top+int(box_height*.15)

    for line in lines[:5]:
        centered(draw, line, y, text_font, width)
        y += line_height

    path = folder/f"scene_{number:02d}.png"
    image.save(path)
    return path


def make_outro(folder, size, short=False):
    width, height = size
    image = Image.new("RGB", size, "#173A6C")
    draw = ImageDraw.Draw(image)

    draw.ellipse(
        (width*.78, height*.05, width*.92, height*.20),
        fill="#FFD94D"
    )
    draw.ellipse(
        (-width*.1, height*.45, width*.5, height*.85),
        fill="#6BC775"
    )
    draw.rectangle(
        (0, height*.70, width, height),
        fill="#4CAF50"
    )

    draw_character(draw, "happy", width, height)

    top = int(height*.25)
    draw.rounded_rectangle(
        (width*.07, top, width*.93, top+height*.28),
        radius=25, fill="#13294B", outline="white", width=4
    )

    heading = "सवाल पसंद आया?" if short else "कहानी अच्छी लगी?"
    centered(
        draw, heading, top+int(height*.04),
        get_font(int(width*.055), True), width
    )

    button_y = top+int(height*.13)
    draw.rounded_rectangle(
        (width*.18, button_y, width*.82, button_y+height*.09),
        radius=22, fill="#E62117", outline="white", width=3
    )
    centered(
        draw, "SUBSCRIBE", button_y+int(height*.02),
        get_font(int(width*.05), True), width
    )
    centered(
        draw, "LIKE  •  SHARE  •  BELL",
        button_y+int(height*.11),
        get_font(int(width*.032), True), width, "#FFE47A"
    )

    path = folder/("short_subscribe.png" if short else "story_subscribe.png")
    image.save(path)
    return path


async def create_voice(text, path):
    voice = edge_tts.Communicate(
        text=text, voice=VOICE, rate="+0%"
    )
    await asyncio.wait_for(voice.save(str(path)), timeout=180)


def duration_of(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path)
        ],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"Could not read audio duration: {path}")

    return max(3.5, float(result.stdout.strip())+0.4)


def make_clip(image, audio, video, duration, size):
    width, height = size
    frames = max(1, int(duration*FPS))

    run_command([
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS),
        "-i", str(image), "-i", str(audio),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='min(zoom+0.00025,1.04)':d={frames}:"
        f"s={width}x{height}:fps={FPS},format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-t", f"{duration:.2f}",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", str(video)
    ])


def combine(clips, destination):
    concat = destination.parent/(destination.stem+"_concat.txt")

    with concat.open("w", encoding="utf-8") as file:
        for clip in clips:
            file.write(f"file '{clip.resolve().as_posix()}'\n")

    if MUSIC.exists():
        run_command([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-stream_loop", "-1", "-i", str(MUSIC),
            "-filter_complex",
            "[1:a]volume=0.10[m];"
            "[0:a][m]amix=inputs=2:duration=first:"
            "dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(destination)
        ])
    else:
        run_command([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c", "copy", "-movflags", "+faststart", str(destination)
        ])


def build_video(scenes, folder, prefix, label, size, short=False):
    clips = []

    for number, (text, kind) in enumerate(scenes, start=1):
        print(f"{prefix}: scene {number}/{len(scenes)}", flush=True)

        image = make_scene(
            text, kind, number, label, size, folder
        )
        audio = folder/f"{prefix}_voice_{number:02d}.mp3"
        clip = folder/f"{prefix}_clip_{number:02d}.mp4"

        asyncio.run(create_voice(text, audio))
        make_clip(image, audio, clip, duration_of(audio), size)
        clips.append(clip)

    outro_image = make_outro(folder, size, short)
    outro_audio = folder/f"{prefix}_outro.mp3"
    outro_clip = folder/f"{prefix}_outro.mp4"

    if short:
        outro_text = "ऐसे मज़ेदार सवालों के लिए चैनल को सब्सक्राइब करें।"
    else:
        outro_text = (
            "ऐसी और मज़ेदार कहानियों के लिए हमारे चैनल को "
            "सब्सक्राइब करें। वीडियो अच्छी लगी हो तो लाइक करें।"
        )

    asyncio.run(create_voice(outro_text, outro_audio))
    make_clip(
        outro_image, outro_audio, outro_clip,
        duration_of(outro_audio), size
    )
    clips.append(outro_clip)

    result = folder/f"{prefix}.mp4"
    combine(clips, result)
    return result


def main():
    for tool in ("ffmpeg", "ffprobe"):
        check = subprocess.run([tool, "-version"], capture_output=True)
        if check.returncode != 0:
            raise RuntimeError(f"{tool} is not installed or not on PATH.")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    folder = OUTPUT/datetime.now().strftime("%Y%m%d_%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)

    story = random.choice(STORIES)
    quiz = random.choice(QUIZZES)

    print("Selected story:", story["title"], flush=True)

    story_scenes = list(story["scenes"])
    story_scenes.append((story["moral"], "happy"))

    # Normal video: native landscape 16:9.
    story_file = build_video(
        story_scenes, folder, "story",
        story["title"], LANDSCAPE, short=False
    )
    (OUTPUT/"daily_video.mp4").write_bytes(story_file.read_bytes())

    # Short: separate quiz, native portrait 9:16.
    quiz_scenes = [
        (quiz["question"], quiz["kind"]),
        (quiz["options"], quiz["kind"]),
        ("सोचने के लिए तीन सेकंड हैं!", quiz["kind"]),
        (quiz["answer"], quiz["kind"])
    ]

    short_file = build_video(
        quiz_scenes, folder, "short",
        "आज का मज़ेदार सवाल", PORTRAIT, short=True
    )
    (OUTPUT/"daily_short.mp4").write_bytes(short_file.read_bytes())

    print("SUCCESS")
    print("Landscape story:", OUTPUT/"daily_video.mp4")
    print("Portrait quiz Short:", OUTPUT/"daily_short.mp4")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR:", error, flush=True)
        raise SystemExit(1)
