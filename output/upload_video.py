
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE = Path(__file__).resolve().parent.parent
OUTPUT = BASE / "output"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def create_youtube():
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES
    )
    credentials.refresh(Request())
    return build("youtube", "v3", credentials=credentials)


def upload(youtube, path, title, description, tags):
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Video missing: {path}")

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

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"{path.name}: {int(status.progress()*100)}%")

    url = "https://www.youtube.com/watch?v=" + response["id"]
    print("Uploaded:", url, flush=True)


def main():
    youtube = create_youtube()
    tags = ["Kya Bache", "Hindi Kids", "Hindi Story", "Hindi Quiz"]

    upload(
        youtube,
        OUTPUT / "daily_video.mp4",
        "पूरी हिंदी कहानी | Kya Bache",
        "बच्चों के लिए पूरी हिंदी कहानी और सीख।",
        tags + ["Full Story"]
    )

    upload(
        youtube,
        OUTPUT / "daily_short.mp4",
        "बच्चों की मज़ेदार पहेली #Shorts",
        "जवाब बताओ! बच्चों के लिए मज़ेदार हिंदी पहेली।",
        tags + ["Shorts", "Riddle"]
    )


if __name__ == "__main__":
    main()
