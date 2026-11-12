from pathlib import Path
import subprocess
import json
import math

OUTPUT = Path("output")
WORK = OUTPUT / "render"
WIDTH, HEIGHT, FPS = 1920, 1080, 24

def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    return result.stdout.strip()

def duration(path):
    value = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ])
    return float(value)

def make_scene(image, audio, output, number):
    seconds = duration(audio) + 0.35
    frames = max(1, int(seconds * FPS))
    # Gentle alternating zoom creates movement without stressing the computer.
    zoom = "1+0.00035*on" if number % 2 == 0 else "1.08-0.00035*on"
    vf = (
        f"scale=2200:1238,zoompan=z='{zoom}':"
        f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "fade=t=in:st=0:d=0.35,format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(image), "-i", str(audio),
        "-t", str(seconds), "-vf", vf, "-r", str(FPS),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "160k", "-shortest", str(output)
    ])

def render_video(image_paths, audio_paths):
    WORK.mkdir(parents=True, exist_ok=True)
    clips = []
    for index, (image, audio) in enumerate(zip(image_paths, audio_paths)):
        clip = WORK / f"clip_{index:02d}.mp4"
        make_scene(image, audio, clip, index)
        clips.append(clip)

    concat_file = WORK / "concat.txt"
    with concat_file.open("w", encoding="utf-8") as handle:
        for clip in clips:
            safe = str(clip.resolve()).replace("'", "'\\''")
            handle.write(f"file '{safe}'\n")

    output_video = OUTPUT / "daily_video.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy", "-movflags", "+faststart", str(output_video)
    ])
    return output_video
