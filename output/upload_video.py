
import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ==========================================
# KYA BACHE - YOUTUBE VIDEO UPLOADER
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")


def get_latest_video():
    """Find the newest generated video."""

    videos = list(OUTPUT_DIR.glob("*/daily_video.mp4"))

    if not videos:
        raise FileNotFoundError(
            "No generated video found in output/<folder>/daily_video.mp4"
        )

    return max(videos, key=lambda path: path.stat().st_mtime)


def get_story_title(video_file):
    """Read the story title from the matching story.json when available."""

    story_file = video_file.parent / "story.json"

    if story_file.exists():
        try:
            with open(story_file, "r", encoding="utf-8") as file:
                story = json.load(file)

            if isinstance(story, dict) and story.get("title"):
                return str(story["title"]).strip()
        except (OSError, json.JSONDecodeError):
            print("Warning: Could not read story.json title.")

    return "Hindi Moral Story for Kids | Kya Bache"


def get_youtube_service():
    """Authenticate using GitHub Actions OAuth secrets."""

    if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
        raise RuntimeError(
            "Missing YouTube OAuth secrets. Configure "
            "YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and "
            "YOUTUBE_REFRESH_TOKEN in GitHub Actions."
        )

    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )

    credentials.refresh(Request())

    return build("youtube", "v3", credentials=credentials)


def upload_video():
    """Upload the latest generated story as a public video."""

    video_file = get_latest_video()
    story_title = get_story_title(video_file)

    title = f"{story_title} | Hindi Kids Story"
    title = title[:100]

    description = """
Enjoy this Hindi children's story from Kya Bache!

Watch our stories for children, friendship, kindness,
good habits, and valuable life lessons.

Subscribe to Kya Bache for more Hindi stories!

#HindiKahani #MoralStories #KidsStories
""".strip()

    tags = [
        "Hindi Kahani",
        "Hindi Moral Stories",
        "Kids Stories",
        "Kya Bache",
        "Hindi Story",
        "Hindi Stories for Kids"
    ]

    print("Connecting to YouTube...")
    youtube = get_youtube_service()

    video_metadata = {
        "snippet": {
            "title": title,
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
        body=video_metadata,
        media_body=media
    )

    print("Uploading video:", video_file.name)
    print("Title:", title)
    print("Requested visibility: Public")

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print("\nUpload completed successfully!")
    print("Video URL:", video_url)
    print("Requested visibility: Public")
    print("Audience setting: Made for kids")


if __name__ == "__main__":
    upload_video()
