
import subprocess
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = OUTPUT_DIR / "temp"
MUSIC_DIR = BASE_DIR / "music"

VIDEO_FILE = OUTPUT_DIR / "daily_video.mp4"

FPS = 25
WIDTH = 1920
HEIGHT = 1080


def run(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg error:\n" + result.stderr[-4000:]
        )


def duration(path):
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    return float(result.stdout.strip())


def make_scene(image, audio, output, number):

    audio_duration = duration(audio)

    # Different camera movement for different scenes.
    scene_number = number if isinstance(number, int) else 13

    zoom_in = scene_number % 2 != 0

    if zoom_in:
        zoom = "min(1.0+0.0006*on,1.08)"
    else:
        zoom = "max(1.08-0.0006*on,1.0)"

    # Slow cinematic horizontal and vertical camera movement.
    pan_x = (
        "(iw-iw/zoom)/2"
        "+(iw-iw/zoom)*0.18*sin(on/120)"
    )

    pan_y = (
        "(ih-ih/zoom)/2"
        "+(ih-ih/zoom)*0.12*cos(on/150)"
    )

    # Subtle colour variation between scenes.
    saturation = 1.10 + (scene_number % 3) * 0.04

    video_filter = (
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,"
        f"zoompan=z='{zoom}':"
        f"x='{pan_x}':"
        f"y='{pan_y}':"
        "d=1:s=1920x1080:fps=25,"
        f"eq=contrast=1.05:saturation={saturation}:brightness=0.01,"
        "unsharp=5:5:0.4:3:3:0.0,"
        "vignette=PI/5,"
        "fade=t=in:st=0:d=0.30,"
        "format=yuv420p"
    )

    audio_filter = "afade=t=in:st=0:d=0.15"

    command = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image),
        "-i", str(audio),

        "-vf", video_filter,
        "-af", audio_filter,

        "-t", str(audio_duration),

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",

        "-threads", "2",
        "-shortest",
        "-movflags", "+faststart",

        str(output)
    ]

    print(f"Rendering cinematic scene {number}...")

    run(command)

    return output


def concatenate_scenes(scene_files, output):

    list_file = TEMP_DIR / "concat_list.txt"

    with open(list_file, "w", encoding="utf-8") as file:

        for scene in scene_files:

            safe_path = Path(scene).resolve().as_posix()
            safe_path = safe_path.replace("'", "'\\\\''")

            file.write(f"file '{safe_path}'\n")

    command = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),

        "-c", "copy",
        "-movflags", "+faststart",

        str(output)
    ]

    print("Combining cinematic scenes...")

    run(command)


def add_background_music(video_file):

    music_files = []

    if MUSIC_DIR.exists():

        for extension in ("*.mp3", "*.wav", "*.m4a"):
            music_files.extend(MUSIC_DIR.glob(extension))

    if not music_files:

        print("No background music found. Keeping narration only.")

        return video_file

    music_file = music_files[0]

    final_file = OUTPUT_DIR / "daily_video_with_music.mp4"

    print("Adding background music...")

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_file),

        "-stream_loop", "-1",
        "-i", str(music_file),

        "-filter_complex",
        (
            "[1:a]volume=0.12[bg];"
            "[0:a][bg]amix=inputs=2:"
            "duration=first:dropout_transition=2[a]"
        ),

        "-map", "0:v",
        "-map", "[a]",

        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",
        "-movflags", "+faststart",

        str(final_file)
    ]

    run(command)

    final_file.replace(video_file)

    return video_file


def render_video(image_paths, audio_paths):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    if len(image_paths) != 12:
        raise ValueError(
            f"Expected 12 images, received {len(image_paths)}"
        )

    if len(audio_paths) != 13:
        raise ValueError(
            f"Expected 13 audio files (12 scenes + moral), "
            f"received {len(audio_paths)}"
        )

    for path in image_paths:

        if not Path(path).is_file():
            raise FileNotFoundError(f"Image missing: {path}")

    for path in audio_paths:

        if not Path(path).is_file():
            raise FileNotFoundError(f"Audio missing: {path}")

    scene_files = []

    # Render all 12 story scenes.
    for index in range(12):

        scene_output = TEMP_DIR / f"scene_{index + 1:02d}.mp4"

        make_scene(
            image_paths[index],
            audio_paths[index],
            scene_output,
            index + 1
        )

        scene_files.append(scene_output)

    # Render the moral scene.
    moral_output = TEMP_DIR / "moral.mp4"

    make_scene(
        image_paths[-1],
        audio_paths[12],
        moral_output,
        "Moral"
    )

    scene_files.append(moral_output)

    # Combine all scenes.
    concatenate_scenes(scene_files, VIDEO_FILE)

    # Add background music.
    add_background_music(VIDEO_FILE)

    print("\nCinematic video created successfully!")
    print("Video:", VIDEO_FILE)

    return str(VIDEO_FILE)
