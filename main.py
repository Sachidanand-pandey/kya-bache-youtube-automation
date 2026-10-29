
import asyncio
import json
import random
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont


# ==========================================
# KYA BACHE - VIDEO GENERATOR
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
WORK_DIR = OUTPUT_DIR / "temp"

STORY_VIDEO = OUTPUT_DIR / "daily_video.mp4"
SHORT_VIDEO = OUTPUT_DIR / "daily_short.mp4"
STORY_METADATA = OUTPUT_DIR / "story_metadata.json"

STORY_WIDTH = 1280
STORY_HEIGHT = 720

SHORT_WIDTH = 720
SHORT_HEIGHT = 1280

VOICE = "hi-IN-SwaraNeural"
FPS = 24


# ==========================================
# CHECK REQUIRED SOFTWARE
# ==========================================

def run_command(command):
    print("Running:", " ".join(str(x) for x in command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr[-4000:])
        raise RuntimeError("Command failed: " + str(command[0]))

    return result.stdout.strip()


def check_ffmpeg():
    run_command(["ffmpeg", "-version"])
    run_command(["ffprobe", "-version"])


# ==========================================
# FONT SETTINGS
# ==========================================

def get_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "C:/Windows/Fonts/mangal.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                pass

    return ImageFont.load_default()


# ==========================================
# DRAW TEXT
# ==========================================

def draw_centered_text(draw, text, y, font, width, fill):
    box = draw.textbbox((0, 0), text, font=font)
    text_width = box[2] - box[0]
    x = (width - text_width) // 2

    draw.text(
        (x + 3, y + 3),
        text,
        font=font,
        fill=(25, 25, 25)
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill
    )


# ==========================================
# DRAW SIMPLE CARTOON CHARACTERS
# ==========================================

def draw_character(draw, character, x, y, scale=1):
    if character == "rabbit":
        body_color = (245, 245, 245)
        draw.ellipse(
            (x - 48 * scale, y - 10 * scale,
             x + 48 * scale, y + 100 * scale),
            fill=body_color,
            outline=(90, 90, 90),
            width=3
        )

        draw.ellipse(
            (x - 38 * scale, y - 95 * scale,
             x - 5 * scale, y - 20 * scale),
            fill=body_color,
            outline=(90, 90, 90),
            width=3
        )

        draw.ellipse(
            (x + 5 * scale, y - 95 * scale,
             x + 38 * scale, y - 20 * scale),
            fill=body_color,
            outline=(90, 90, 90),
            width=3
        )

        draw.ellipse(
            (x - 35 * scale, y - 45 * scale,
             x + 35 * scale, y + 25 * scale),
            fill=body_color,
            outline=(90, 90, 90),
            width=3
        )

        draw.ellipse(
            (x - 18 * scale, y - 22 * scale,
             x - 10 * scale, y - 14 * scale),
            fill=(20, 20, 20)
        )

        draw.ellipse(
            (x + 10 * scale, y - 22 * scale,
             x + 18 * scale, y - 14 * scale),
            fill=(20, 20, 20)
        )

        draw.ellipse(
            (x - 6 * scale, y - 7 * scale,
             x + 6 * scale, y + 3 * scale),
            fill=(240, 100, 130)
        )

    elif character == "monkey":
        draw.ellipse(
            (x - 50 * scale, y - 10 * scale,
             x + 50 * scale, y + 100 * scale),
            fill=(145, 85, 45)
        )

        draw.ellipse(
            (x - 45 * scale, y - 70 * scale,
             x + 45 * scale, y + 20 * scale),
            fill=(145, 85, 45)
        )

        draw.ellipse(
            (x - 28 * scale, y - 40 * scale,
             x + 28 * scale, y + 5 * scale),
            fill=(240, 190, 135)
        )

        draw.ellipse(
            (x - 23 * scale, y - 35 * scale,
             x - 13 * scale, y - 25 * scale),
            fill=(20, 20, 20)
        )

        draw.ellipse(
            (x + 13 * scale, y - 35 * scale,
             x + 23 * scale, y - 25 * scale),
            fill=(20, 20, 20)
        )

    elif character == "bird":
        draw.ellipse(
            (x - 45 * scale, y - 45 * scale,
             x + 45 * scale, y + 45 * scale),
            fill=(55, 150, 245)
        )

        draw.polygon(
            [
                (x + 40 * scale, y - 5 * scale),
                (x + 75 * scale, y + 5 * scale),
                (x + 40 * scale, y + 15 * scale)
            ],
            fill=(255, 175, 20)
        )

        draw.ellipse(
            (x - 20 * scale, y - 20 * scale,
             x - 10 * scale, y - 10 * scale),
            fill=(255, 255, 255)
        )

        draw.ellipse(
            (x - 16 * scale, y - 18 * scale,
             x - 12 * scale, y - 12 * scale),
            fill=(20, 20, 20)
        )

    else:
        draw.ellipse(
            (x - 45 * scale, y - 45 * scale,
             x + 45 * scale, y + 45 * scale),
            fill=(255, 185, 50)
        )


# ==========================================
# CREATE VIDEO SCENE IMAGE
# ==========================================

def create_scene_image(
    filename,
    width,
    height,
    title,
    story_text,
    character,
    scene_number
):
    image = Image.new("RGB", (width, height), (145, 210, 255))
    draw = ImageDraw.Draw(image)

    # Sky
    draw.rectangle(
        (0, 0, width, int(height * 0.65)),
        fill=(135, 205, 255)
    )

    # Sun
    draw.ellipse(
        (width - 140, 40, width - 60, 120),
        fill=(255, 220, 70)
    )

    # Hills
    draw.ellipse(
        (-width // 3, int(height * 0.40),
         width // 2, int(height * 0.85)),
        fill=(95, 195, 95)
    )

    draw.ellipse(
        (width // 3, int(height * 0.43),
         width + width // 3, int(height * 0.88)),
        fill=(65, 170, 85)
    )

    # Ground
    draw.rectangle(
        (0, int(height * 0.72), width, height),
        fill=(75, 160, 70)
    )

    # Story character
    character_y = int(height * 0.60)

    if character == "tree":
        tree_x = width // 2
        tree_y = int(height * 0.52)

        draw.rectangle(
            (tree_x - 22, tree_y,
             tree_x + 22, tree_y + int(height * 0.23)),
            fill=(120, 75, 35)
        )

        draw.ellipse(
            (tree_x - 105, tree_y - 105,
             tree_x + 105, tree_y + 45),
            fill=(35, 155, 65)
        )

        draw.ellipse(
            (tree_x - 65, tree_y - 135,
             tree_x + 65, tree_y - 5),
            fill=(45, 180, 75)
        )

        draw.ellipse(
            (tree_x - 20, tree_y - 65,
             tree_x + 20, tree_y - 25),
            fill=(255, 220, 40)
        )

    else:
        scale = min(width / 1000, height / 1000) * 1.4
        draw_character(
            draw,
            character,
            width // 2,
            character_y,
            scale
        )

    # Title banner
    draw.rounded_rectangle(
        (20, 20, width - 20, int(height * 0.16)),
        radius=20,
        fill=(35, 70, 145)
    )

    draw_centered_text(
        draw,
        title,
        30,
        get_font(max(20, int(width * 0.035))),
        width,
        (255, 255, 255)
    )

    # Scene narration caption
    banner_y = int(height * 0.82)

    draw.rounded_rectangle(
        (20, banner_y, width - 20, height - 18),
        radius=18,
        fill=(255, 255, 255)
    )

    caption_font = get_font(max(18, int(width * 0.027)))

    # Split the caption into lines.
    words = story_text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word

        if draw.textbbox(
            (0, 0), test_line, font=caption_font
        )[2] > width - 80:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test_line.strip()

    if current_line:
        lines.append(current_line)

    line_height = max(24, int(width * 0.035))
    start_y = banner_y + 10

    for line in lines[:2]:
        draw_centered_text(
            draw,
            line,
            start_y,
            caption_font,
            width,
            (30, 40, 70)
        )
        start_y += line_height

    image.save(filename)


# ==========================================
# STORY LIBRARY
# ==========================================

STORIES = [
    {
        "title": "जादुई पेड़ का रहस्य",
        "character": "rabbit",
        "scenes": [
            "एक दिन खरगोश को जंगल में एक रहस्यमयी पेड़ मिला।",
            "पेड़ पर चमकते फल थे, लेकिन खरगोश ने उन्हें नहीं तोड़ा।",
            "तभी एक छोटी चिड़िया ने बताया कि पेड़ प्यासा है।",
            "खरगोश ने पेड़ की जड़ों में पानी डाला।",
            "पेड़ पर मीठे फल उग आए और सभी जानवर खुश हो गए।"
        ],
        "moral": "सीख: प्रकृति की देखभाल करना अच्छी बात है।"
    },
    {
        "title": "ईमानदार बंदर",
        "character": "monkey",
        "scenes": [
            "एक बंदर को जंगल में आमों से भरी टोकरी मिली।",
            "वह आम खाना चाहता था, लेकिन उसने मालिक को ढूँढा।",
            "थोड़ी दूर उसे एक भूखा खरगोश दिखाई दिया।",
            "बंदर ने टोकरी खरगोश को लौटा दी।",
            "खरगोश ने खुशी से आम सबके साथ बाँट लिए।"
        ],
        "moral": "सीख: ईमानदारी और बाँटना अच्छी आदतें हैं।"
    },
    {
        "title": "नीली चिड़िया की मदद",
        "character": "bird",
        "scenes": [
            "एक छोटी नीली चिड़िया बारिश में रास्ता भटक गई।",
            "वह पेड़ के नीचे बैठकर अपने घर को याद करने लगी।",
            "एक दयालु खरगोश ने उसे सुरक्षित रास्ता दिखाया।",
            "चिड़िया खुशी से उड़कर अपने घोंसले पहुँची।",
            "अगले दिन चिड़िया अपने नए दोस्त से मिलने आई।"
        ],
        "moral": "सीख: दूसरों की मदद करने से दोस्ती बढ़ती है।"
    }
]


# ==========================================
# QUIZ LIBRARY
# ==========================================

QUIZZES = [
    {
        "question": "कौन सा जानवर जंगल का राजा कहलाता है?",
        "options": ["हाथी", "शेर", "खरगोश"],
        "answer": "शेर",
        "fact": "शेर को जंगल का राजा कहा जाता है।"
    },
    {
        "question": "कौन सा फल पीला होता है?",
        "options": ["केला", "अंगूर", "तरबूज"],
        "answer": "केला",
        "fact": "केला एक लोकप्रिय पीला फल है।"
    },
    {
        "question": "रात में आसमान में क्या चमकता है?",
        "options": ["चाँद", "कुर्सी", "जूता"],
        "answer": "चाँद",
        "fact": "चाँद रात के आसमान में दिखाई दे सकता है।"
    }
]


# ==========================================
# CREATE HINDI AUDIO
# ==========================================

async def create_audio(text, filename):
    communication = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="-5%"
    )

    await communication.save(str(filename))


def get_audio_duration(filename):
    duration = run_command([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(filename)
    ])

    return float(duration)


# ==========================================
# BUILD VIDEO FROM SCENES
# ==========================================

def create_scene_video(image_path, audio_path, output_path):
    duration = get_audio_duration(audio_path) + 0.4

    run_command([
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),
        "-i", str(audio_path),
        "-t", str(duration),
        "-vf", (
            "scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
            "format=yuv420p"
        ),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "24",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output_path)
    ])


def create_short_scene_video(image_path, audio_path, output_path):
    duration = get_audio_duration(audio_path) + 0.4

    run_command([
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),
        "-i", str(audio_path),
        "-t", str(duration),
        "-vf", (
            "scale=720:1280:force_original_aspect_ratio=decrease,"
            "pad=720:1280:(ow-iw)/2:(oh-ih)/2,"
            "format=yuv420p"
        ),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "24",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output_path)
    ])


def join_videos(video_files, output_file):
    list_file = WORK_DIR / "concat_list.txt"

    with list_file.open("w", encoding="utf-8") as file:
        for video in video_files:
            escaped_path = str(video.resolve()).replace("'", "'\\''")
            file.write("file '" + escaped_path + "'\n")

    run_command([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_file)
    ])


# ==========================================
# GENERATE FULL LANDSCAPE STORY
# ==========================================

async def generate_story():
    story = random.choice(STORIES)

    scene_videos = []

    for index, scene_text in enumerate(story["scenes"]):
        print("Creating story scene", index + 1)

        image_path = WORK_DIR / ("story_image_" + str(index) + ".png")
        audio_path = WORK_DIR / ("story_audio_" + str(index) + ".mp3")
        video_path = WORK_DIR / ("story_scene_" + str(index) + ".mp4")

        create_scene_image(
            image_path,
            STORY_WIDTH,
            STORY_HEIGHT,
            story["title"],
            scene_text,
            story["character"],
            index
        )

        await create_audio(scene_text, audio_path)
        create_scene_video(image_path, audio_path, video_path)

        scene_videos.append(video_path)

    # Add the moral as the final scene.
    moral_image = WORK_DIR / "story_moral.png"
    moral_audio = WORK_DIR / "story_moral.mp3"
    moral_video = WORK_DIR / "story_moral.mp4"

    create_scene_image(
        moral_image,
        STORY_WIDTH,
        STORY_HEIGHT,
        story["title"],
        story["moral"],
        story["character"],
        99
    )

    await create_audio(story["moral"], moral_audio)
    create_scene_video(moral_image, moral_audio, moral_video)

    scene_videos.append(moral_video)

    join_videos(scene_videos, STORY_VIDEO)

    with STORY_METADATA.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "title": story["title"],
                "moral": story["moral"],
                "character": story["character"]
            },
            file,
            ensure_ascii=False,
            indent=2
        )

    print("Full story created:", STORY_VIDEO)


# ==========================================
# GENERATE PORTRAIT QUIZ SHORT
# ==========================================

async def generate_quiz_short():
    quiz = random.choice(QUIZZES)

    short_scenes = [
        (
            "आज का मज़ेदार सवाल!",
            quiz["question"]
        ),
        (
            "तीन विकल्पों में से चुनें",
            "पहला: " + quiz["options"][0]
            + ". दूसरा: " + quiz["options"][1]
            + ". तीसरा: " + quiz["options"][2]
        ),
        (
            "सही जवाब है!",
            quiz["answer"] + "। " + quiz["fact"]
        )
    ]

    scene_videos = []

    for index, scene in enumerate(short_scenes):
        heading, narration = scene

        image_path = WORK_DIR / ("quiz_image_" + str(index) + ".png")
        audio_path = WORK_DIR / ("quiz_audio_" + str(index) + ".mp3")
        video_path = WORK_DIR / ("quiz_scene_" + str(index) + ".mp4")

        create_scene_image(
            image_path,
            SHORT_WIDTH,
            SHORT_HEIGHT,
            heading,
            narration,
            "bird",
            index
        )

        await create_audio(narration, audio_path)
        create_short_scene_video(image_path, audio_path, video_path)

        scene_videos.append(video_path)

    join_videos(scene_videos, SHORT_VIDEO)

    print("Quiz Short created:", SHORT_VIDEO)


# ==========================================
# MAIN
# ==========================================

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    check_ffmpeg()

    await generate_story()
    await generate_quiz_short()

    if not STORY_VIDEO.exists() or STORY_VIDEO.stat().st_size == 0:
        raise RuntimeError("Story video was not generated.")

    if not SHORT_VIDEO.exists() or SHORT_VIDEO.stat().st_size == 0:
        raise RuntimeError("Quiz Short was not generated.")

    print("================================")
    print("Kya Bache video generation done.")
    print("Story:", STORY_VIDEO)
    print("Short:", SHORT_VIDEO)
    print("================================")


if __name__ == "__main__":
    asyncio.run(main())
