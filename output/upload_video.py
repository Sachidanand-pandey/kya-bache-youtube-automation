
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not client_id or not client_secret or not refresh_token:
        raise RuntimeError("Missing YouTube OAuth secrets.")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    credentials.refresh(Request())

    return build(
        "youtube",
        "v3",
        credentials=credentials
    )


def upload_video(youtube, path, title, description, tags):
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {path}")

    body = {
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
        str(path),
        mimetype="video/mp4",
        chunksize=5 * 1024 * 1024,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    print("Uploading:", path.name, flush=True)

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            print(
                "Upload progress:",
                int(status.progress() * 100),
                "%",
                flush=True
            )

    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"

    print("Uploaded successfully:", url, flush=True)
    return url


def main():
    vertical_file = OUTPUT_DIR / "daily_video.mp4"
    landscape_file = OUTPUT_DIR / "daily_video_landscape.mp4"

    youtube = get_youtube_service()

    tags = [
        "Kya Bache",
        "Hindi Kahani",
        "Hindi Moral Stories",
        "Kids Stories",
        "Hindi Story"
    ]

    short_url = upload_video(
        youtube,
        vertical_file,
        "नीली चिड़िया की कहानी | Hindi Story #Shorts",
        "बच्चों के लिए प्यारी हिंदी कहानी। "
        "ऐसी और कहानियों के लिए चैनल को सब्सक्राइब करें। "
        "#Shorts #HindiKahani #KidsStories",
        tags + ["Shorts"]
    )

    print("VERTICAL VIDEO URL:", short_url, flush=True)

    landscape_url = upload_video(
        youtube,
        landscape_file,
        "नीली चिड़िया की पूरी कहानी | Hindi Kids Story",
        "बच्चों के लिए पूरी हिंदी कहानी और सीख। "
        "नई कहानियों के लिए Kya Bache को सब्सक्राइब करें।",
        tags + ["Full Story"]
    )

    print("LANDSCAPE VIDEO URL:", landscape_url, flush=True)


if __name__ == "__main__":
    main()
