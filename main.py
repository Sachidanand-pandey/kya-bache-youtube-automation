
import os
import json
import subprocess
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_latest_video():
    videos = list(OUTPUT_DIR.glob("*/daily_video.mp4"))

    if not videos:
        raise FileNotFoundError(
            "No generated daily_video.mp4 found."
        )

    return max(videos, key=lambda p: p.stat().st_mtime)


def get_story_title(video_file):
    story_file = video_file.parent / "story.json"

    if story_file.exists():
        try:
            with story_file.open("r", encoding="utf-8") as f:
                story = json.load(f)
            if story.get("title"):
                return str(story["title"]).strip()
        except (OSError, json.JSONDecodeError):
            pass

    return "Hindi Moral Story for Kids | Kya Bache"


def create_landscape(vertical_file):
    landscape_file = vertical_file.parent / "daily_video_landscape.mp4"

    command = [
        "ffmpeg", "-y",
        "-i", str(vertical_file),
        "-filter_complex",
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,boxblur=20:10[background];"
        "[fg]scale=607:1080:force_original_aspect_ratio=decrease,"
        "setsar=1[foreground];"
        "[background][foreground]overlay=(W-w)/2:(H-h)/2,"
        "format=yuv420p[v]",
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(landscape_file)
    ]

    print("Creating landscape version...")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Landscape conversion failed:\n"
            + result.stderr[-3000:]
        )

    return landscape_file


def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not client_id or not client_secret or not refresh_token:
        raise RuntimeError(
            "Missing YouTube OAuth secrets in GitHub Actions."
        )

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    credentials.refresh(Request())

    return build("youtube", "v3", credentials=credentials)


def upload_one(youtube, video_file, title, description, tags):
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "22",
            "defaultLanguage": "hi"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": True
        }
    }

    media = MediaFileUpload(
        str(video_file),
        mimetype="video/mp4",
        chunksize=5 * 1024 * 1024,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=metadata,
        media_body=media
    )

    print("Uploading:", title)

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            print(
                "Upload progress:",
                int(status.progress() * 100),
                "%"
            )

    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"

    print("Upload successful:", url)
    return url


def main():
    vertical_file = get_latest_video()
    story_title = get_story_title(vertical_file)

    # Create the horizontal version from the vertical video.
    landscape_file = create_landscape(vertical_file)

    youtube = get_youtube_service()

    tags = [
        "Hindi Kahani",
        "Hindi Moral Stories",
        "Kids Stories",
        "Kya Bache",
        "Hindi Story"
    ]

    short_url = upload_one(
        youtube,
        vertical_file,
        f"{story_title} | Hindi Story #Shorts",
        "Watch this Hindi children's story from Kya Bache!\n"
        "Subscribe for more Hindi stories.\n"
        "#Shorts #HindiKahani #KidsStories",
        tags + ["Shorts"]
    )

    print("SHORT URL:", short_url)

    landscape_url = upload_one(
        youtube,
        landscape_file,
        f"{story_title} | Full Hindi Story",
        "Enjoy the Hindi children's story from Kya Bache!\n"
        "Subscribe for more Hindi stories and moral lessons.",
        tags + ["Full Story"]
    )

    print("REGULAR VIDEO URL:", landscape_url)


if __name__ == "__main__":
    main()
