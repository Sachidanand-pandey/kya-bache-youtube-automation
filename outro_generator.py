
import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import edge_tts


WIDTH = 1280
HEIGHT = 720

VOICE = "hi-IN-SwaraNeural"

OUTRO_TEXT = (
    "बच्चों, अगर आपको यह कहानी अच्छी लगी हो, "
    "तो वीडियो को लाइक करें, अपने दोस्तों के साथ शेयर करें "
    "और ऐसी ही मज़ेदार कहानियों के लिए हमारे चैनल को सब्सक्राइब करें। "
    "फिर मिलेंगे एक नई कहानी के साथ। धन्यवाद!"
)


# Hindi font available on your Windows computer
def get_hindi_font(size):
    font_path = r"C:\Windows\Fonts\Nirmala.ttc"

    if Path(font_path).exists():
        return ImageFont.truetype(font_path, size)

    raise FileNotFoundError(
        "Hindi font Nirmala.ttc not found."
    )


# Create outro image
def create_outro_image(image_path):

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        "#FFF0C2"
    )

    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (35, 35, 1245, 685),
        radius=45,
        fill="white"
    )

    draw.rounded_rectangle(
        (70, 65, 1210, 205),
        radius=35,
        fill="#FFE08A"
    )

    title_font = get_hindi_font(55)
    body_font = get_hindi_font(36)

    button_font = ImageFont.truetype(
        r"C:\Windows\Fonts\arialbd.ttf",
        34
    )

    title = "कहानी अच्छी लगी?"

    box = draw.textbbox(
        (0, 0),
        title,
        font=title_font
    )

    draw.text(
        ((WIDTH - (box[2] - box[0])) / 2, 105),
        title,
        font=title_font,
        fill="#713B00"
    )

    # Like, Subscribe and Share buttons
    buttons = [
        ((150, 330, 430, 445), "#E53935", "LIKE"),
        ((500, 330, 780, 445), "#2EAD62", "SUBSCRIBE"),
        ((850, 330, 1130, 445), "#2878D0", "SHARE")
    ]

    for coords, color, label in buttons:

        draw.rounded_rectangle(
            coords,
            radius=28,
            fill=color
        )

        box = draw.textbbox(
            (0, 0),
            label,
            font=button_font
        )

        text_width = box[2] - box[0]
        text_height = box[3] - box[1]

        x = coords[0] + (
            coords[2] - coords[0] - text_width
        ) / 2

        y = coords[1] + (
            coords[3] - coords[1] - text_height
        ) / 2 - 5

        draw.text(
            (x, y),
            label,
            font=button_font,
            fill="white"
        )

    footer = "नई कहानियों के लिए चैनल को सब्सक्राइब करें!"

    box = draw.textbbox(
        (0, 0),
        footer,
        font=body_font
    )

    draw.text(
        ((WIDTH - (box[2] - box[0])) / 2, 520),
        footer,
        font=body_font,
        fill="#333333"
    )

    image.save(image_path)


# Generate Hindi voice
async def create_hindi_audio(audio_path):

    voice = edge_tts.Communicate(
        OUTRO_TEXT,
        VOICE,
        rate="+0%",
        volume="+0%"
    )

    await voice.save(str(audio_path))


# Execute FFmpeg
def run_ffmpeg(command):

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg error:\n" + result.stderr[-4000:]
        )


# Add outro to original video
def add_outro(video_path):

    video_path = Path(video_path).resolve()

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg is not installed or not in PATH."
        )

    folder = video_path.parent

    image_path = folder / "outro_card.png"
    audio_path = folder / "outro_audio.mp3"
    outro_video = folder / "outro_clip.mp4"

    final_video = folder / "daily_video_with_outro.mp4"

    print("Creating outro image...")

    create_outro_image(image_path)

    print("Generating Hindi voice...")

    asyncio.run(
        create_hindi_audio(audio_path)
    )

    print("Creating 15-second outro video...")

    run_ffmpeg([
        ffmpeg, "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-t", "15",
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-af", "apad",
        "-shortest",
        str(outro_video)
    ])

    print("Combining original video and outro...")

    run_ffmpeg([
        ffmpeg, "-y",
        "-i", str(video_path),
        "-i", str(outro_video),
        "-filter_complex",

        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25[v0];"

        "[1:v]scale=1280:720,setsar=1,fps=25[v1];"

        "[0:a]aresample=44100,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"

        "[1:a]aresample=44100,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo[a1];"

        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",

        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(final_video)
    ])

    print("\nSUCCESS!")
    print("Final video:", final_video)


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage: python outro_generator.py "
            "output/daily_video.mp4"
        )

        sys.exit(1)

    add_outro(sys.argv[1])
